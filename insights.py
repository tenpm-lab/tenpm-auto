# -*- coding: utf-8 -*-
"""
tenpm.lab 쓰레드 성과 자동 수집 (매일 밤 GitHub에서 실행)

  stats/posts.csv    글별 조회수·좋아요·댓글·리포스트·인용·공유 (매일 한 줄씩 쌓임)
  stats/account.csv  계정 팔로워 수 (매일 한 줄)

필요한 권한: threads_basic, threads_manage_insights
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.threads.net/v1.0"
KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
STATS = os.path.join(HERE, "stats")
POST_METRICS = "views,likes,replies,reposts,quotes,shares"


def get(path, params):
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"({e.code}) {e.read().decode('utf-8', errors='replace')}")


def notify(title, message):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return
    try:
        req = urllib.request.Request("https://ntfy.sh/" + topic, data=message.encode("utf-8"),
                                     headers={"Title": title.encode("utf-8"), "Tags": "bar_chart"}, method="POST")
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print("알림 실패:", e)


def values(data):
    out = {}
    for m in data.get("data", []):
        if "values" in m and m["values"]:
            out[m["name"]] = m["values"][-1].get("value", 0)
        elif "total_value" in m:
            out[m["name"]] = m["total_value"].get("value", 0)
    return out


def append(path, header, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerows(rows)


def main():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    if not token:
        sys.exit("THREADS_TOKEN 없음")
    os.makedirs(STATS, exist_ok=True)
    today = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    # 1) 최근 글 목록 (이어쓰기 답글은 목록에 안 나옴 = 첫 글 기준)
    posts, after = [], None
    for _ in range(4):  # 최대 100개
        p = {"fields": "id,text,timestamp,permalink", "limit": 25, "access_token": token}
        if after:
            p["after"] = after
        res = get("/me/threads", p)
        posts += res.get("data", [])
        after = res.get("paging", {}).get("cursors", {}).get("after")
        if not after or not res.get("data"):
            break

    # 2) 글별 인사이트
    rows, failed = [], None
    for post in posts:
        try:
            v = values(get(f"/{post['id']}/insights", {"metric": POST_METRICS, "access_token": token}))
        except RuntimeError as e:
            failed = str(e)
            break
        first = (post.get("text") or "").split("\n")[0][:40]
        ts = post.get("timestamp", "")[:16].replace("T", " ")
        rows.append([today, post["id"], ts, first] + [v.get(k, 0) for k in POST_METRICS.split(",")] + [post.get("permalink", "")])

    if failed:
        print("❌ 인사이트 권한이 없거나 오류:", failed)
        notify("⚠️ 인사이트 수집 실패", "토큰에 인사이트 권한이 없을 수 있어요\nAI 대화창에 '인사이트 실패'라고 보내줘")
        sys.exit(1)

    append(os.path.join(STATS, "posts.csv"),
           ["수집시각", "글ID", "올린시각(UTC)", "첫줄"] + POST_METRICS.split(",") + ["링크"], rows)

    # 3) 계정 팔로워
    followers = ""
    try:
        acc = values(get("/me/threads_insights", {"metric": "followers_count", "access_token": token}))
        followers = acc.get("followers_count", "")
    except RuntimeError as e:
        print("팔로워 수 실패:", e)
    append(os.path.join(STATS, "account.csv"), ["수집시각", "팔로워"], [[today, followers]])

    top = sorted(rows, key=lambda r: r[4] or 0, reverse=True)[:3]
    msg = f"글 {len(rows)}개 · 팔로워 {followers}\n" + "\n".join(f"{r[4]}회 · {r[3][:20]}" for r in top)
    print(msg)
    if os.environ.get("NOTIFY_SUMMARY") == "1":
        notify("📊 오늘의 쓰레드 성과", msg)


if __name__ == "__main__":
    main()
