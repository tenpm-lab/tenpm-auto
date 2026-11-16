# -*- coding: utf-8 -*-
"""
쿠팡파트너스 클릭·주문·수익 자동 수집 (매일 밤 GitHub에서 실행)
  stats/coupang_daily.csv   날짜별 클릭/주문/수익 (최근 14일을 매번 새로 받아 덮어씀)
  stats/coupang_raw/*.json  API 원본 (subId별 분석용)
비밀값: COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY (GitHub Secrets)
"""
import csv
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

HOST = "https://api-gateway.coupang.com"
BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1"
KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
STATS = os.path.join(HERE, "stats")


def auth(method, path, query, ak, sk):
    dt = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
    msg = dt + method + path + query
    sig = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ak}, signed-date={dt}, signature={sig}"


def call(method, path, query="", body=None):
    ak = os.environ["COUPANG_ACCESS_KEY"].strip()
    sk = os.environ["COUPANG_SECRET_KEY"].strip()
    url = HOST + path + ("?" + query if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": auth(method, path, query, ak, sk),
        "Content-Type": "application/json;charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"({e.code}) {e.read().decode(errors='replace')[:300]}")


def notify(title, message):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://ntfy.sh/" + topic, data=message.encode(),
            headers={"Title": title.encode(), "Tags": "moneybag"}, method="POST"), timeout=20).read()
    except Exception as e:
        print("알림 실패:", e)


def num(row, *keys):
    for k in keys:
        if k in row and row[k] not in (None, ""):
            try:
                return float(row[k])
            except (TypeError, ValueError):
                pass
    return 0


def main():
    if not os.environ.get("COUPANG_ACCESS_KEY") or not os.environ.get("COUPANG_SECRET_KEY"):
        print("쿠팡 API 키 없음 → 건너뜀")
        return
    os.makedirs(os.path.join(STATS, "coupang_raw"), exist_ok=True)
    end = datetime.now(KST).date()
    start = end - timedelta(days=13)
    q = f"startDate={start:%Y%m%d}&endDate={end:%Y%m%d}"

    days = {}
    for kind in ("clicks", "orders", "commission"):
        try:
            res = call("GET", f"{BASE}/reports/{kind}", q)
        except RuntimeError as e:
            print(f"❌ {kind} 실패:", e)
            notify("⚠️ 쿠팡 수집 실패", f"{kind}: {str(e)[:80]}\nAI 대화창에 '쿠팡 실패'라고 보내줘")
            sys.exit(1)
        with open(os.path.join(STATS, "coupang_raw", f"{kind}_{end:%Y%m%d}.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        for row in res.get("data") or []:
            d = str(row.get("date", ""))[:8]
            day = days.setdefault(d, {"click": 0, "order": 0, "gmv": 0, "commission": 0})
            if kind == "clicks":
                day["click"] += num(row, "click", "clickCount")
            elif kind == "orders":
                day["order"] += num(row, "orderCount", "quantity", "order")
                day["gmv"] += num(row, "gmv", "orderPrice", "amount")
            else:
                day["commission"] += num(row, "commission", "commissionAmount")

    path = os.path.join(STATS, "coupang_daily.csv")
    old = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            for r in list(csv.reader(f))[1:]:
                old[r[0]] = r
    for d, v in days.items():
        old[d] = [d, int(v["click"]), int(v["order"]), int(v["gmv"]), int(v["commission"])]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["날짜", "클릭", "주문", "주문금액", "수익"])
        w.writerows(sorted(old.values()))

    week = [v for d, v in days.items() if d >= f"{end - timedelta(days=6):%Y%m%d}"]
    msg = (f"최근 7일 클릭 {int(sum(v['click'] for v in week))} · 주문 {int(sum(v['order'] for v in week))}"
           f" · 수익 {int(sum(v['commission'] for v in week)):,}원")
    print(msg)
    if os.environ.get("NOTIFY_SUMMARY") == "1":
        notify("💰 쿠팡파트너스", msg)


if __name__ == "__main__":
    main()
