# -*- coding: utf-8 -*-
"""쿠팡 API 창구별로 원래 가격·할인율 필드가 있는지 한 번 확인 (결과: curate/probe.json, url·코드 저장 안 함)"""
import json, os, re, urllib.request, urllib.parse
from coupang_stats import BASE, call
HERE = os.path.dirname(os.path.abspath(__file__))
def items(res):
    d = res.get("data") if isinstance(res, dict) else res
    if isinstance(d, dict):
        d = d.get("productData") or d.get("data") or d
    return d if isinstance(d, list) else ([d] if d else [])
def clean(x):
    return {k: v for k, v in x.items() if "url" not in k.lower()} if isinstance(x, dict) else str(x)[:200]
out = {}
tests = [
    ("goldbox", "GET", f"{BASE}/products/goldbox", "subId=probe", None),
    ("best_1001", "GET", f"{BASE}/products/bestcategories/1001", "limit=3&subId=probe", None),
    ("search", "GET", f"{BASE}/products/search", "keyword=" + urllib.parse.quote("휴지") + "&limit=3&subId=probe", None),
    ("coupangPL", "GET", f"{BASE}/products/coupangPL", "limit=3&subId=probe", None),
    ("reco_get", "GET", f"{BASE}/products/reco", "subId=probe", None),
    ("reco_post", "POST", f"{BASE}/products/reco", "", {"site": {"id": "probe"}, "device": {"id": "probe", "lmt": 0}, "imp": {"imageSize": "200x200"}, "user": {"puid": "probe"}}),
]
pid = None
for name, m, path, q, body in tests:
    try:
        res = call(m, path, q, body) if body else call(m, path, q)
        its = items(res)
        keys = sorted({k for it in its if isinstance(it, dict) for k in it})
        out[name] = {"count": len(its), "keys": keys, "sample": clean(its[0]) if its else None,
                     "top": sorted(res.keys()) if isinstance(res, dict) else None}
        if not pid and its and isinstance(its[0], dict):
            pid = its[0].get("productId")
    except Exception as e:
        out[name] = {"error": str(e)[:200]}
pages = {}
for label, url in [("mobile", f"https://m.coupang.com/vm/products/{pid}"),
                   ("mobile_goldbox", "https://m.coupang.com/nm/goldbox"),
                   ("pc_goldbox", "https://pages.coupang.com/p/121237")]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148", "Accept-Language": "ko-KR"})
        with urllib.request.urlopen(req, timeout=20) as r:
            h = r.read().decode("utf-8", "ignore")
        pages[label] = {"status": 200, "len": len(h), "price_hits": re.findall(r'(?:origin|base|original|discount)[A-Za-z_-]*["\':=\s>]{1,4}[^<"]{0,30}', h)[:6]}
    except Exception as e:
        pages[label] = {"error": str(e)[:120]}
out["pages"] = pages
json.dump(out, open(os.path.join(HERE, "curate", "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
