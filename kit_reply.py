# -*- coding: utf-8 -*-
"""본계정 AI 사무실 → 가이드 무료 배포, 댓글 자동 답장 (11/26)
1단계 관심 글(파일 이름에 _officekit): "궁금해요" 같은 댓글에 "가이드 만들어볼까" 답글, 관심 댓글 기록(stats/kit_interest.txt)
  - 관심 댓글이 실제로 5개 넘으면 "생각보다 반응 좋네.. 가이드 만들어봐야겠다" (사실일 때만)
  (11/26 Ssuii: "나 궁금해! 이런 댓글들 달리면 너가 자동으로 생각보다 쉬운데 가이드를 한번 만들어볼까? 이런식으로 댓글 달아보는거지")
  - kit/open_post.txt 에 2단계 신청 글 주소를 넣으면, 관심 댓글 단 사람들에게 "신청 글 올렸어요" 답글 한 번
2단계 신청 글(파일 이름에 _kitopen)에 '키트'·'신청' 같은 댓글이 달리면:
- 키트 완성 전: "신청 완료" 답글 + 신청 순서 기록 (stats/kit_signups.txt, 댓글 ID와 시간만 — 아이디는 저장 안 함)
- 키트 완성 후 (kit/beta_link.txt 에 주소를 넣으면): 앞 5명에게 무료 베타 링크 답글
- 6번째부터는 '2차 베타'로 등록 (거절 대신 순서만 뒤로). kit/beta2_link.txt 에 주소를 넣으면 2차에게도 링크 답글
  (11/26 Ssuii: "베타 다 찼고, 정식으로 알려줄게 하면 속상해서 떠나지 않으려나..")
한 번 돌 때 최대 5개, 같은 댓글엔 한 번만. post.yml 이 15분마다 부름.
"""
import os, random, sys
from datetime import datetime, timedelta, timezone

from post_queue import call, publish

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posts", "posted_log.txt")
SIGN = os.path.join(HERE, "stats", "kit_signups.txt")   # 댓글ID \t 시간 \t 상태(접수/베타/대기)
LINKF = os.path.join(HERE, "kit", "beta_link.txt")
LINK2F = os.path.join(HERE, "kit", "beta2_link.txt")
KST = timezone(timedelta(hours=9))
WANT = ("키트", "신청", "저요", "써보고", "써볼", "원해", "원합", "희망", "받고 싶", "받고싶", "참여")
BETA = 5
MAX_PER_RUN = 5
GOT = ["신청 완료! {n}번째 🙌\n키트 완성되면 이 댓글에 답글로 알려줄게",
       "접수됨 ✅ ({n}번째)\n만들어지면 여기로 바로 알려줌",
       "{n}번째 신청 고마워요 🙏\n완성되면 답글 달아줄게"]
BETA_MSG = ["무료 베타 자리 왔어요 🎉\n{l}\n막히는 데 있으면 여기 답글로 알려줘",
            "베타 키트 여기! 👉 {l}\n써보고 막히는 곳 알려주면 설명서 고칠게"]
WAIT_MSG = ["1차는 다 찼어요 🙏 ({n}번째 신청)\n2차 추가 배포는 공지 글로 따로 올리고 이 댓글에도 알려줄게",
            "{n}번째 신청 고마워요! 1차는 마감됐고\n2차 추가 배포 공지는 따로 올릴게. 여기에도 답글 남겨줄게 🙌"]
BETA2_MSG = ["2차 베타 차례 왔어요 🎉\n{l}\n막히는 데 있으면 여기 답글로 알려줘",
             "기다려줘서 고마워요 🙏 2차 베타 키트 👉 {l}"]


def kit_posts(tag="_kitopen"):
    ids = []
    try:
        for line in open(LOG, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and tag in p[1]:
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


INTEREST = os.path.join(HERE, "stats", "kit_interest.txt")   # 댓글ID \t 시간 \t 상태(관심/안내함)
OPENF = os.path.join(HERE, "kit", "open_post.txt")
CURIOUS = ("궁금", "알려", "방법", "어떻게", "나도", "저도", "가이드", "만들고 싶", "만들고싶", "해보고 싶", "해보고싶",
           "공유", "부럽", "키트", "신청", "저요", "배우고", "강의", "ㄱㄱ", "원해", "갖고 싶", "갖고싶")
EARLY = ["생각보다 진짜 쉬움 ㅋㅋ\n궁금한 사람 좀 모이면 가이드로 정리해볼까 생각 중",
         "AI한테 시키는 순서만 알면 됨!\n가이드 한번 만들어볼까 싶네 🤔",
         "나도 처음엔 어려울 줄 알았는데 생각보다 금방 됨 😆\n정리해서 풀어볼까 고민 중"]
MANY = ["생각보다 반응이 좋네..\n가이드 한번 만들어봐야겠다 🔥",
        "궁금한 사람이 꽤 많네 ㅋㅋ\n가이드 정리해볼게! 올리면 여기 답글로 알려줄게",
        "이 정도면 만들어야겠다 ㅋㅋ\n가이드 나오면 이 댓글로 알려줄게 🙌"]
OPEN_MSG = ["가이드 무료 배포 신청 받는 중 🙌\n{l}", "말했던 가이드 신청 글 올렸어요!\n{l}"]


def interest(token, me):
    posts = kit_posts("_officekit")
    if not posts:
        return 0
    rd = lambda f: open(f, encoding="utf-8").read().strip() if os.path.exists(f) else ""
    rows = [l.split("\t") for l in rd(INTEREST).splitlines() if l.count("\t") == 2]
    seen = {r[0] for r in rows}; sent = 0
    for pid in posts:
        conv = call("GET", f"/{pid}/conversation",
                    {"fields": "id,text,username,timestamp", "limit": 100, "access_token": token}).get("data", [])
        conv.sort(key=lambda c: c.get("timestamp", ""))
        for c in conv:
            if sent >= MAX_PER_RUN:
                break
            cid, who, text = c["id"], c.get("username"), (c.get("text") or "")
            if who in (None, me["username"]) or cid in seen or not any(w in text for w in CURIOUS):
                continue
            msg = random.choice(MANY if len(rows) >= 5 else EARLY)   # 5명 넘게 실제로 관심 보였을 때만 "반응 좋네"
            try:
                publish(token, me["id"], msg, [], cid, ""); sent += 1
                rows.append([cid, datetime.now(KST).strftime("%m/%d %H:%M"), "관심"]); seen.add(cid)
                print("관심 댓글 답장", len(rows))
            except Exception as e:
                print("답장 실패", str(e)[:100])
    url = rd(OPENF)
    if url:
        for r in rows:
            if sent >= MAX_PER_RUN:
                break
            if r[2] != "관심":
                continue
            try:
                publish(token, me["id"], random.choice(OPEN_MSG).format(l=url), [], r[0], ""); sent += 1; r[2] = "안내함"
            except Exception as e:
                print("답장 실패", str(e)[:100])
    if rows:
        os.makedirs(os.path.dirname(INTEREST), exist_ok=True)
        open(INTEREST, "w", encoding="utf-8").write("".join("\t".join(r) + "\n" for r in rows))
    print("관심 댓글", len(rows), "개 · 이번에 답장", sent, "개")
    return sent


def main():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    if not token:
        return
    me = call("GET", "/me", {"fields": "id,username", "access_token": token})
    interest(token, me)
    posts = kit_posts()
    if not posts:
        print("키트 신청: 신청 글 아직 없음"); return
    rd = lambda f: open(f, encoding="utf-8").read().strip() if os.path.exists(f) else ""
    link, link2 = rd(LINKF), rd(LINK2F)
    rows = load(); seen = {r[0] for r in rows}
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
            if link and n <= BETA:
                msg, state = random.choice(BETA_MSG).format(l=link), "베타"
            elif link2 and n > BETA:
                msg, state = random.choice(BETA2_MSG).format(l=link2), "2차받음"
            elif link:
                msg, state = random.choice(WAIT_MSG).format(n=n), "2차대기"
            else:
                msg, state = random.choice(GOT).format(n=n), "접수"
            try:
                reply(cid, msg)
                rows.append([cid, datetime.now(KST).strftime("%m/%d %H:%M"), state]); seen.add(cid)
                print("키트 신청 답장", n, state)
            except Exception as e:
                print("답장 실패", str(e)[:100])
    # 2) 링크가 생기면, 먼저 접수한 사람들에게 순서대로
    for i, r in enumerate(rows):
        if sent >= MAX_PER_RUN:
            break
        msg = None
        if r[2] == "접수" and link:
            msg, new = (random.choice(BETA_MSG).format(l=link), "베타") if i < BETA else (random.choice(WAIT_MSG).format(n=i+1), "2차대기")
        if r[2] in ("접수", "2차대기") and i >= BETA and link2:
            msg, new = random.choice(BETA2_MSG).format(l=link2), "2차받음"
        if not msg:
            continue
        try:
            reply(r[0], msg); r[2] = new
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
