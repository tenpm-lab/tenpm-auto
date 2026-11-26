# -*- coding: utf-8 -*-
"""댓글 자동 답장
내 최근 글(3일 안)에 달린 댓글 중, replies.json 에 적은 단어가 들어간 댓글에만 답글을 단다.
- 한 댓글에 한 번만 (stats/replied.txt), 한 번 돌 때 최대 5개 — 스팸처럼 보이지 않게
- 답글 문구는 여러 개 중 하나를 골라서 매번 조금씩 다르게
- replies.json 이 비어 있으면 아무것도 안 함
GitHub에서 15분마다 예약 게시와 같이 돈다.
"""
import json, os, random, sys
from datetime import datetime, timedelta, timezone

from post_queue import call, publish

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "replies.json")
REPLIED = os.path.join(HERE, "stats", "replied.txt")
MAX_PER_RUN = 5
DAYS = 3


def main():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    if not token or not os.path.exists(RULES):
        print("토큰이나 replies.json 없음 - 건너뜀"); return
    rules = [r for r in json.load(open(RULES, encoding="utf-8")).get("규칙", []) if r.get("단어") and r.get("답글")]
    if not rules:
        print("답장 규칙 없음"); return
    done = set(open(REPLIED, encoding="utf-8").read().split()) if os.path.exists(REPLIED) else set()
    me = call("GET", "/me", {"fields": "id,username", "access_token": token})
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime("%Y-%m-%dT%H:%M")
    mine = call("GET", "/me/threads", {"fields": "id,timestamp", "limit": 25, "access_token": token}).get("data", [])
    sent = 0
    for post in mine:
        if post.get("timestamp", "")[:16] < cutoff:
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
            rule = next((r for r in rules if any(w in text for w in r["단어"])), None)
            if not rule:
                continue
            try:
                publish(token, me["id"], random.choice(rule["답글"]), [], cid, "")
                sent += 1
                print("답장:", text[:20])
            except Exception as e:
                print("답장 실패", str(e)[:100])
            done.add(cid)
    os.makedirs(os.path.dirname(REPLIED), exist_ok=True)
    open(REPLIED, "w", encoding="utf-8").write("\n".join(sorted(done)) + "\n")
    print("자동 답장", sent, "개")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 답장이 실패해도 글 올리기는 막지 않게
        print("자동 답장 건너뜀:", str(e)[:150])
        sys.exit(0)
