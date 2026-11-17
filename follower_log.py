# -*- coding: utf-8 -*-
"""15분마다 팔로워 수를 확인해서 '바뀌었을 때만' stats/followers.csv 에 한 줄 남김.
주간 리포트가 이걸로 '팔로워가 늘기 직전에 올라간 글'을 찾아줌 (11/17~)."""
import csv, json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "stats", "followers.csv")
T = os.environ.get("THREADS_TOKEN", "").strip()
if not T:
    raise SystemExit(0)
url = "https://graph.threads.net/v1.0/me/threads_insights?" + urllib.parse.urlencode({"metric": "followers_count", "access_token": T})
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        d = json.load(r)
    m = d["data"][0]
    n = int(m["total_value"]["value"] if "total_value" in m else m["values"][-1]["value"])
except Exception as e:
    print("팔로워 확인 실패(넘어감):", str(e)[:80]); raise SystemExit(0)
last = None
if os.path.exists(P):
    rows = list(csv.reader(open(P, encoding="utf-8-sig")))
    if len(rows) > 1:
        last = int(rows[-1][1])
if last != n:
    new = not os.path.exists(P)
    with open(P, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new: w.writerow(["시각(KST)", "팔로워"])
        w.writerow([datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"), n])
    print(f"팔로워 {last} → {n}")
else:
    print(f"팔로워 그대로 {n}")
