# -*- coding: utf-8 -*-
"""
쿠팡파트너스 '상품 검색 API'로 모음 페이지 상품의 현재 가격·대표 사진을 가져옴.
  - 상품명(또는 items.json 의 "kw")으로 검색 → 결과 중 productId 가 우리 링크와 같은 것만 사용
  - 결과는 bio/product_info.json 에 저장 (productId → 가격, 사진, 시각)
  - 검색 API는 1시간에 호출 수 제한이 있어 한 번에 최대 9개, 오래된 것부터 갱신
"""
import json, os, re, sys, urllib.parse
from datetime import datetime, timedelta, timezone
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from coupang_stats import call  # 같은 인증 코드 재사용

KST = timezone(timedelta(hours=9))
SPEC = json.load(open(os.path.join(HERE, "bio", "items.json"), encoding="utf-8"))
P = os.path.join(HERE, "bio", "product_info.json")
info = json.load(open(P, encoding="utf-8")) if os.path.exists(P) else {}
MAX = int(os.environ.get("MAX_CALLS", "40"))
SEARCH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"

items = [it for c in SPEC["cats"] for it in c["items"]]
def pid(it):
    m = re.search(r"/products/(\d+)", it.get("url", ""))
    return m.group(1) if m else None
todo = [it for it in items if pid(it)]
todo.sort(key=lambda it: (info.get(pid(it), {}).get("ok", False), info.get(pid(it), {}).get("ts", "")))  # 안 가져온 것·오래된 것 먼저
now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
log = []
calls = 0
stop = False
for it in todo:
    p = pid(it)
    kws = it.get("kw") or []
    if isinstance(kws, str): kws = [kws]
    cur = info.get(p, {})
    if cur.get("ok") and cur.get("kw_used"):
        cand = [cur["kw_used"]]                      # 이미 찾은 상품은 같은 검색어로 가격만 갱신
    else:
        tried = cur.get("tried", [])
        cand = [k for k in list(kws) + [it["name"]] if k not in tried]
    for kw in cand:
        if calls >= MAX or stop: break
        calls += 1
        try:
            r = call("GET", SEARCH, "keyword=" + urllib.parse.quote(kw) + "&limit=10")
        except Exception as e:
            log.append(f"{it['name']}: 오류 {e}")
            if "429" in str(e) or "limit" in str(e).lower(): stop = True
            continue
        found = next((x for x in ((r.get("data") or {}).get("productData") or []) if str(x.get("productId")) == p), None)
        if found:
            info[p] = {"name": it["name"], "price": found.get("productPrice"), "image": found.get("productImage"),
                       "title": found.get("productName"), "ts": now, "ok": True, "kw_used": kw,
                       "item_id": (re.search(r"itemId=(\d+)", found.get("productUrl", "")) or [None, None])[1]}
            log.append(f"{it['name']}: {found.get('productPrice')}원 ('{kw}')")
            break
        cur = info.setdefault(p, {})
        top = ((r.get("data") or {}).get("productData") or [None])[0]
        if top and not cur.get("approx"):   # 같은 상품을 못 찾으면 비슷한 상품 1위 가격을 참고용으로
            cur["approx"] = top.get("productPrice")
        cur.update({"name": it["name"], "ts": now, "ok": False})
        cur["tried"] = cur.get("tried", []) + [kw]
        log.append(f"{it['name']}: '{kw}' 결과에 없음")
json.dump(info, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(HERE, "bio", "fetch_log.txt"), "w", encoding="utf-8").write(now + "\n" + "\n".join(log) + "\n")
print("\n".join(log))
