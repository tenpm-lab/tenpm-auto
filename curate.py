# -*- coding: utf-8 -*-
"""
할인 상품 후보 모으기 (쿠팡파트너스 API)
  python curate.py
→ curate/today.json : 후보 목록 (상품번호·이름·가격·할인 정보·사진 파일·짧은 파트너 링크)
→ images/curate/<상품번호>.jpg : 상품 대표 사진
원본 응답(raw)과 긴 파트너 링크(AF 코드 들어 있음)는 저장하지 않는다.
"""
import datetime
import json
import os
import urllib.parse
import urllib.request

from coupang_stats import BASE, call

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "curate", "today.json")
IMG = os.path.join(HERE, "images", "curate")
KST = datetime.timezone(datetime.timedelta(hours=9))
SKIP = ("성인", "콘돔", "의약", "영양제", "다이어트", "건강기능", "담배", "주류")


def items_of(res):
    d = res.get("data") if isinstance(res, dict) else res
    if isinstance(d, dict):
        d = d.get("productData") or d.get("data") or []
    return d or []


def main():
    os.makedirs(IMG, exist_ok=True)
    now = datetime.datetime.now(KST)
    got = items_of(call("GET", f"{BASE}/products/goldbox", "subId=curate"))
    keys = sorted({k for it in got for k in it.keys()})
    out = []
    for it in got:
        name = str(it.get("productName", ""))
        if any(w in name for w in SKIP):
            continue
        pid = str(it.get("productId", ""))
        row = {k: it.get(k) for k in keys if k not in ("productUrl",) and "url" not in k.lower()}
        row["source"] = "goldbox"
        # 사진
        img = it.get("productImage")
        if img and pid:
            try:
                req = urllib.request.Request(img, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r, open(os.path.join(IMG, pid + ".jpg"), "wb") as f:
                    f.write(r.read())
                row["image_file"] = f"images/curate/{pid}.jpg"
            except Exception as e:
                row["image_error"] = str(e)[:80]
        row.pop("productImage", None)
        # 짧은 파트너 링크 (글마다 꼬리표)
        try:
            sub = "cu" + now.strftime("%m%d") + pid[-5:]
            res = call("POST", f"{BASE}/deeplink",
                       body={"coupangUrls": [f"https://www.coupang.com/vp/products/{pid}"], "subId": sub})
            d = items_of(res)
            if d:
                row["short_link"] = d[0].get("shortenUrl")
                row["subId"] = sub
        except Exception as e:
            row["link_error"] = str(e)[:80]
        out.append(row)
    # 가격 기록 (할인율 직접 계산용): 날짜·상품번호·이름·가격만
    hist = os.path.join(HERE, "curate", "prices.jsonl")
    with open(hist, "a", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps({"t": now.strftime("%Y-%m-%d %H:%M"), "pid": str(r.get("productId")),
                                "name": str(r.get("productName"))[:60], "price": r.get("productPrice")},
                               ensure_ascii=False) + "\n")
    # 시험: 쿠팡 상품 페이지에서 원래 가격(취소선) 읽을 수 있는지 3개만 확인
    probe = []
    for r in out[:3]:
        pid = str(r.get("productId"))
        try:
            req = urllib.request.Request(f"https://www.coupang.com/vp/products/{pid}",
                                         headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ko-KR"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", "ignore")
            import re
            hits = re.findall(r'(origin-price|base-price|discount-rate|original-price)[^<]{0,80}<?[^<]{0,40}', html)[:5]
            probe.append({"pid": pid, "status": 200, "len": len(html), "hits": hits})
        except Exception as e:
            probe.append({"pid": pid, "error": str(e)[:80]})
    json.dump(probe, open(os.path.join(HERE, "curate", "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"fetched_at": now.strftime("%Y-%m-%d %H:%M"), "fields": keys, "items": out},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "items; fields:", keys)


if __name__ == "__main__":
    main()
