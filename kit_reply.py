# -*- coding: utf-8 -*-
"""본계정 '키트' 신청 댓글 자동 답장 (11/26)
수요 확인 글(파일 이름에 _officekit 이 들어간 글)에 '키트' 같은 신청 댓글이 달리면:
- 키트 완성 전: "신청 완료" 답글 + 신청 순서 기록 (stats/kit_signups.txt, 댓글 ID와 시간만 — 아이디는 저장 안 함)
- 키트 완성 후 (kit/beta_link.txt 에 주소를 넣으면): 앞 5명에게 무료 베타 링크 답글, 그 뒤는 정식 오픈 안내
한 번 돌 때 최대 5개, 같은 댓글엔 한 번만. post.yml 이 15분마다 부름.
"""
import os, random, sys
from datetime import datetime, timedelta, timezone

from post_queue import call, publish

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posts", "posted_log.txt")
SIGN = os.path.join(HERE, "stats", "kit_signups.txt")   # 댓글ID \t 시간 \t 상태(접수/베타/대기)
LINKF = os.path.join(HERE, "kit", "beta_link.txt")
KST = timezone(timedelta(hours=9))
WANT = ("키트", "신청", "저요", "써보고", "써볼", "원해", "원합", "희망", "받고 싶", "받고싶", "참여")
BETA = 5
MAX_PER_RUN = 5
GOT = ["신청 완료! {n}번째 🙌\n키트 완성되면 이 댓글에 답글로 알려줄게",
       "접수됨 ✅ ({n}번째)\n만들어지면 여기로 바로 알려줌",
       "{n}번째 신청 고마워요 🙏\n완성되면 답글 달아줄게"]
BETA_MSG = ["무료 베타 자리 왔어요 🎉\n{l}\n막히는 데 있으면 여기 답글로 알려줘",
            "베타 키트 여기! 👉 {l}\n써보고 막히는 곳 알려주면 설명서 고칠게"]
WAIT_MSG = ["베타 5자리가 다 찼어요 🙏\n정식으로 열면 이 댓글에 알려줄게"]


def kit_posts():
    ids = []
    try:
        for line in open(LOG, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and "_officekit" in p[1]:
                ids.append(p[2].split(",")[0])
    except FileNotFoundError:
        pass
    return ids


def load():
    rows = []
    if os.path.exists(SIGN):
        for line in open(SIGN, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) == 3:
                rows.append(p)
    return rows


def main():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    posts = kit_posts()
    if not token or not posts:
        print("키트 신청: 대상 글 없음"); return
    link = open(LINKF, encoding="utf-8").read().strip() if os.path.exists(LINKF) else ""
    rows = load(); seen = {r[0] for r in rows}
    me = call("GET", "/me", {"fields": "id,username", "access_token": token})
    sent = 0

    def reply(cid, text):
        nonlocal sent
        publish(token, me["id"], text, [], cid, ""); sent += 1

    # 1) 새 신청 댓글
    for pid in posts:
        conv = call("GET", f"/{pid}/conversation",
                    {"fields": "id,text,username,timestamp", "limit": 100, "access_token": token}).get("data", [])
        conv.sort(key=lambda c: c.get("timestamp", ""))
        for c in conv:
            if sent >= MAX_PER_RUN:
                break
            cid, who, text = c["id"], c.get("username"), (c.get("text") or "")
            if who in (None, me["username"]) or cid in seen or not any(w in text for w in WANT):
                continue
            n = len(rows) + 1
            if link:
                msg = random.choice(BETA_MSG if n <= BETA else WAIT_MSG).format(l=link)
                state = "베타" if n <= BETA else "대기"
            else:
                msg, state = random.choice(GOT).format(n=n), "접수"
            try:
                reply(cid, msg)
                rows.append([cid, datetime.now(KST).strftime("%m/%d %H:%M"), state]); seen.add(cid)
                print("키트 신청 답장", n, state)
            except Exception as e:
                print("답장 실패", str(e)[:100])
    # 2) 링크가 생기면, 먼저 접수한 사람들에게 순서대로
    if link:
        for i, r in enumerate(rows):
            if sent >= MAX_PER_RUN:
                break
            if r[2] != "접수":
                continue
            beta = i < BETA
            try:
                reply(r[0], random.choice(BETA_MSG if beta else WAIT_MSG).format(l=link))
                r[2] = "베타" if beta else "대기"
            except Exception as e:
                print("답장 실패", str(e)[:100])
    os.makedirs(os.path.dirname(SIGN), exist_ok=True)
    if rows:
        open(SIGN, "w", encoding="utf-8").write("".join("\t".join(r) + "\n" for r in rows))
    print("키트 신청", len(rows), "명 · 이번에 답장", sent, "개")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("키트 답장 건너뜀:", str(e)[:150])
        sys.exit(0)
