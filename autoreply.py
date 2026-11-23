# -*- coding: utf-8 -*-
"""부계정 댓글 자동 답장 (11/23)
"어디서 사요?", "링크요", "제품명 뭐예요?" 처럼 사고 싶어서 묻는 댓글에만, 그 글의 쿠팡 링크를 답글로 단다.
- 링크가 있는 글(posts/deal/done 의 파일)에 단 댓글만. 워밍업 질문 글처럼 링크 없는 글은 손대지 않음.
- 한 댓글에 한 번만 (stats/deal/replied.txt), 한 번 돌 때 최대 5개 — 스팸처럼 보이지 않게.
- 답글에도 광고 표시.
post.yml 이 15분마다 부를 때 같이 돈다 (THREADS_TOKEN = 부계정 토큰, ACCOUNT=deal).
"""
import os, random, re, sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("ACCOUNT", "deal")
from post_queue import call, publish  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DONE = os.path.join(HERE, "posts", "deal", "done")
LOG = os.path.join(HERE, "posts", "deal", "posted_log.txt")
REPLIED = os.path.join(HERE, "stats", "deal", "replied.txt")
LINK = re.compile(r"https://link\.coupang\.com/a/\w+")
# 사고 싶어서 묻는 말
WANT = ("링크", "ㄹㅋ", "어디서", "어디 ", "어디꺼", "어디거", "어디서사", "제품명", "상품명", "모델명", "정보", "구매", "살 수", "사고싶", "사고 싶",
        "주문", "판매", "얼마", "가격", "알려주", "공유", "브랜드", "이름이", "뭐예요", "뭐에요", "뭔가요", "궁금")
MAX_PER_RUN = 5
# 답글은 매번 조금씩 다르게 (11/23 Ssuii: "답변도 매번 조금씩 다르게 하는거지?")
REPLIES = [
    "여기 있음 👉 {l}",
    "링크 여기! 👉 {l}",
    "이거임 👇\n{l}",
    "요기서 보면 됨 👉 {l}",
    "바로 가는 링크 👉 {l}",
    "찾던 거 여기 있음 👀\n{l}",
    "여기서 가격까지 볼 수 있음 👉 {l}",
]


def post_links():
    """글 ID → 그 글 파일의 첫 쿠팡 링크"""
    out = {}
    try:
        for line in open(LOG, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            f = os.path.join(DONE, p[1])
            if os.path.exists(f):
                links = LINK.findall(open(f, encoding="utf-8").read())
                if links:
                    out[p[2]] = links[0]
    except FileNotFoundError:
        pass
    return out


def main():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    if not token:
        print("부계정 토큰 없음"); return
    links = post_links()
    if not links:
        print("링크 있는 글 없음"); return
    done = set(open(REPLIED, encoding="utf-8").read().split()) if os.path.exists(REPLIED) else set()
    me = call("GET", "/me", {"fields": "id,username", "access_token": token})
    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    mine = call("GET", "/me/threads", {"fields": "id,timestamp", "limit": 25, "access_token": token}).get("data", [])
    sent = 0
    for post in mine:
        if post["id"] not in links or post.get("timestamp", "")[:16] < cutoff:
            continue
        conv = call("GET", f"/{post['id']}/conversation",
                    {"fields": "id,text,username,replied_to", "limit": 100, "access_token": token}).get("data", [])
        answered = {(c.get("replied_to") or {}).get("id") for c in conv if c.get("username") == me["username"]}
        for c in conv:
            if sent >= MAX_PER_RUN:
                break
            cid, who, text = c["id"], c.get("username"), (c.get("text") or "")
            if who in (None, me["username"]) or cid in done or cid in answered:
                continue
            if not any(w in text.replace("  ", " ") for w in WANT):
                continue
            reply = random.choice(REPLIES).format(l=links[post['id']]) + "\n(쿠팡 파트너스 활동으로 수수료를 받을 수 있음)"
            try:
                publish(token, me["id"], reply, [], cid, "")
                sent += 1
                print("답장", who, text[:20])
            except Exception as e:
                print("답장 실패", str(e)[:100])
            done.add(cid)
    if sent or done:
        os.makedirs(os.path.dirname(REPLIED), exist_ok=True)
        open(REPLIED, "w", encoding="utf-8").write("\n".join(sorted(done)) + "\n")
    print("자동 답장", sent, "개")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 답장 실패가 게시를 막지 않게
        print("자동 답장 건너뜀:", str(e)[:150])
        sys.exit(0)
