# -*- coding: utf-8 -*-
"""
'써본 것만 모음' 페이지 만들기 → docs/index.html (GitHub Pages)
site/items.json 을 읽어 상품마다 꼬리표 subId "bio" 쿠팡 링크를 만들고 (만든 건 site/links_bio.json 에 저장해 재사용)
"""
import html, json, os, sys
from coupang_stats import BASE, call
from coupang_links import resolve

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "bio", "items.json"), encoding="utf-8"))
CACHE_P = os.path.join(HERE, "bio", "links_bio.json")
cache = json.load(open(CACHE_P, encoding="utf-8")) if os.path.exists(CACHE_P) else {}
opened = 0
errors = []

for cat in SPEC["cats"]:
    for it in cat["items"]:
        key = it.get("url") or it.get("short")
        if key in cache:
            it["link"] = cache[key]
            continue
        try:
            url = it.get("url")
            if not url:
                url = resolve(it["short"]); opened += 1
            res = call("POST", f"{BASE}/deeplink", body={"coupangUrls": [url], "subId": "bio"})
            link = (res.get("data") or [{}])[0].get("shortenUrl", "")
            if not link:
                raise RuntimeError(str(res)[:200])
            it["link"] = cache[key] = link
            print("✓", it["name"], link)
        except Exception as ex:
            errors.append(f"{it['name']}: {str(ex)[:200]}")
            it["link"] = it.get("short") or it.get("url")  # 실패하면 원래 링크로
json.dump(cache, open(CACHE_P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if opened:
    with open(os.path.join(HERE, "stats", "bot_clicks.csv"), "a", encoding="utf-8") as f:
        from datetime import datetime, timedelta, timezone
        f.write(f"{datetime.now(timezone(timedelta(hours=9))):%Y-%m-%d},{opened},모음 페이지 만들 때 예전 짧은 링크 열어봄(make_site.py)\n")

from PIL import Image
os.makedirs(os.path.join(HERE, "docs", "img"), exist_ok=True)
for cat in SPEC["cats"]:
    for it in cat["items"]:
        src = os.path.join(HERE, "images", it.get("img", ""))
        if it.get("img") and os.path.exists(src):
            im = Image.open(src).convert("RGB")
            w, h = im.size; s0 = min(w, h)
            im = im.crop(((w - s0) // 2, (h - s0) // 2, (w + s0) // 2, (h + s0) // 2)).resize((480, 480))
            im.save(os.path.join(HERE, "docs", "img", it["img"]), quality=80)

e = html.escape
_ip = os.path.join(HERE, "bio", "product_info.json")
INFO = json.load(open(_ip, encoding="utf-8")) if os.path.exists(_ip) else {}
def price_of(it):
    import re as _re
    m = _re.search(r"/products/(\d+)(?:.*itemId=(\d+))?", it.get("url", ""))
    d = INFO.get(m.group(1), {}) if m else {}
    api = int(float(d["price"])) if d.get("ok") and d.get("price") else None
    if api and m.group(2) and d.get("item_id") == m.group(2):
        return api
    return it.get("price") or api or (int(float(d["approx"])) if d.get("approx") else None)
cards = []
for cat in SPEC["cats"]:
    rows = []
    for it in cat["items"]:
        pay = '<span class="pay">리뷰 페이백</span>' if it.get("payback") else ""
        img = f'<img src="img/{e(it["img"])}" alt="{e(it["name"])}" loading="lazy">' if it.get("img") else ""
        rows.append(f'<a class="item" href="{e(it["link"])}" target="_blank" rel="sponsored noopener">{pay}{img}'
                    f'<div class="body"><div class="say">{e(it["say"])}</div><div class="name">{e(it["name"])}</div>'
                    + (f'<div class="price">{price_of(it):,}원</div>' if price_of(it) else '')
                    + f'<div class="go">보러 가기 ›</div></div></a>')
    cards.append(f'<section id="c{len(cards)}"><h2>{e(cat["name"])} <span class="cnt">{len(rows)}</span></h2><div class="grid">{"".join(rows)}</div></section>')

page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(SPEC['title'])} · tenpm.lab</title>
<style>
:root{{--bg:#fbf4ea;--ink:#3b2f2a;--sub:#8c7b70;--acc:#d9764f;--card:#fff;--line:#eadfd1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}
main{{max-width:720px;margin:0 auto;padding:28px 16px 60px}}
header{{text-align:center;padding:10px 0 6px}}
.avatar{{width:76px;height:76px;border-radius:50%;background:#12141b;display:inline-flex;align-items:center;justify-content:center}}
.avatar svg{{width:46px;height:46px}}
h1{{font-size:24px;margin:12px 0 6px}}.handle{{color:var(--acc);font-weight:700;font-size:14px}}
.intro{{color:var(--sub);font-size:14px;line-height:1.6;margin:8px auto 14px;max-width:440px}}
.links{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:14px}}
.links a{{background:#fff;border:1px solid var(--line);border-radius:99px;padding:8px 14px;font-size:13px;font-weight:700;color:var(--ink);text-decoration:none}}
.notice{{font-size:11.5px;color:var(--sub);background:#f3e8da;border-radius:12px;padding:10px 12px;line-height:1.55}}
nav{{position:sticky;top:0;background:var(--bg);display:flex;gap:6px;overflow-x:auto;padding:12px 0 8px;z-index:2}}
nav a{{flex:none;background:#fff;border:1px solid var(--line);border-radius:99px;padding:6px 12px;font-size:13px;color:var(--ink);text-decoration:none}}
h2{{font-size:18px;margin:22px 0 10px}}.cnt{{color:var(--acc);font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}
@media(min-width:620px){{.grid{{grid-template-columns:repeat(3,1fr)}}}}
.item{{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column}}
.item img{{width:100%;aspect-ratio:1;object-fit:cover;display:block;background:#eee}}
.body{{padding:10px 11px 12px;display:flex;flex-direction:column;gap:4px;flex:1}}
.say{{font-weight:800;font-size:15px;line-height:1.38;color:var(--ink)}}
.name{{color:var(--sub);font-size:12.5px}}
.item{{position:relative}}.price{{font-weight:800;font-size:14px;color:var(--ink);margin-top:3px}}.pay{{position:absolute;top:8px;left:8px;background:rgba(255,255,255,.92);color:#8a6f5a;font-size:11px;font-weight:700;padding:3px 8px;border-radius:999px;z-index:1}}
.price{{font-weight:800;font-size:14px;margin-top:2px}}.price.muted{{color:var(--sub);font-weight:600;font-size:12px}}
.go{{margin-top:auto;padding-top:6px;color:var(--acc);font-weight:800;font-size:12.5px}}
.tags{{display:flex;gap:4px;flex-wrap:wrap}}.tags:empty{{display:none}}
.tag{{font-size:10.5px;font-weight:700;color:var(--acc);border:1px solid var(--acc);border-radius:99px;padding:1px 6px}}
.tag.soft{{color:var(--sub);border-color:var(--line)}}
footer{{margin-top:30px;font-size:12px;color:var(--sub);line-height:1.6;text-align:center}}
</style></head><body><main>
<header>
<div class="avatar"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="38" fill="none" stroke="#f5f5f5" stroke-width="9"/><line x1="50" y1="50" x2="50" y2="24" stroke="#f5f5f5" stroke-width="9" stroke-linecap="round"/><line x1="50" y1="50" x2="69" y2="59" stroke="#f5c400" stroke-width="9" stroke-linecap="round"/></svg></div>
<h1>{e(SPEC['title'])}</h1>
<div class="handle">@tenpm.lab</div>
<p class="intro">{e(SPEC['intro'])}</p>
<div class="links"><a href="https://www.threads.com/@tenpm.lab">쓰레드</a><a href="https://blog.naver.com/tenpmlab">블로그</a></div>
</header>
<p class="notice">이 페이지의 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. 가격은 바뀔 수 있어요.<br>
‘리뷰 페이백’ 표시 제품은 구매 후 리뷰 작성 대가로 구매 금액을 돌려받았어요.</p>
<nav>{"".join(f'<a href="#c{i}">{e(c["name"])}</a>' for i, c in enumerate(SPEC["cats"]))}</nav>
{"".join(cards)}
<footer>매일 밤 10시 실험 기록 → 쓰레드 @tenpm.lab<br>
<a href="https://blog.naver.com/tenpmlab">블로그 · 텐피엠 퇴근 후 AI 부업</a></footer>
</main></body></html>"""
open(os.path.join(HERE, "bio", "build_log.txt"), "w", encoding="utf-8").write("\n".join(errors) or "오류 없음")
os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
open(os.path.join(HERE, "docs", "index.html"), "w", encoding="utf-8").write(page)
print("페이지 완성:", sum(len(c["items"]) for c in SPEC["cats"]), "개")
