# -*- coding: utf-8 -*-
"""이미 올라간 글에 이어 쓰기(링크 댓글)만 다는 일회용 도구.
fix/reply.txt: 첫 줄 = 대상 글 첫 줄, '---' 아래 = 달 댓글"""
import os
from post_queue import call, publish
token = os.environ["THREADS_TOKEN"]
raw = open("fix/reply.txt", encoding="utf-8").read()
target, reply = raw.split("\n---\n", 1)
target = target.strip()
uid = call("GET", "/me", {"fields": "id", "access_token": token})["id"]
posts = call("GET", "/me/threads", {"fields": "id,text,timestamp", "limit": "10", "access_token": token}).get("data", [])
hit = [p for p in posts if (p.get("text") or "").strip().startswith(target)]
if not hit:
    raise SystemExit("대상 글을 못 찾음")
pid = hit[0]["id"]
rid = publish(token, uid, reply.strip(), [], pid, "")
print("댓글 달림:", pid, "->", rid)
open("fix/reply.txt", "w").write("")
