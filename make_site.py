# -*- coding: utf-8 -*-
"""
'써본 것만 모음' 페이지 만들기 → docs/index.html (GitHub Pages)
site/items.json 을 읽어 상품마다 꼬리표 subId "bio" 쿠팡 링크를 만들고 (만든 건 site/links_bio.json 에 저장해 재사용)
"""
import html, json, os, sys
from coupang_stats import BASE, call
from coupang_links import resolve

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "site", "items.json"), encoding="utf-8"))
CACHE_P = os.path.join(HERE, "site", "links_bio.json")
cache = json.load(open(CACHE_P, encoding="utf-8")) if os.path.exists(CACHE_P) else {}
opened = 0

for cat in SPEC["cats"]:
    for it in cat["items"]:
        key = it.get("url") or it.get("short")
        if key in cache:
            it["link"] = cache[key]
            continue
        url = it.get("url")
        if not url:
            url = resolve(it["short"]); opened += 1
        res = call("POST", f"{BASE}/deeplink", body={"coupangUrls": [url], "subId": "bio"})
        it["link"] = cache[key] = (res.get("data") or [{}])[0].get("shortenUrl", "")
        print("✓", it["name"], it["link"])
json.dump(cache, open(CACHE_P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if opened:
    with open(os.path.join(HERE, "stats", "bot_clicks.csv"), "a", encoding="utf-8") as f:
        from datetime import datetime, timedelta, timezone
        f.write(f"{datetime.now(timezone(timedelta(hours=9))):%Y-%m-%d},{opened},모음 페이지 만들 때 예전 짧은 링크 열어봄(make_site.py)\n")

e = html.escape
cards = []
for cat in SPEC["cats"]:
    rows = []
    for it in cat["items"]:
        tags = ""
        if it.get("payback"): tags += '<span class="tag">페이백</span>'
        if it.get("similar"): tags += '<span class="tag soft">비슷한 상품</span>'
        rows.append(f'<a class="item" href="{e(it["link"])}" target="_blank" rel="sponsored noopener">'
                    f'<div><div class="name">{e(it["name"])}{tags}</div><div class="say">{e(it["say"])}</div></div>'
                    f'<div class="go">보기 ›</div></a>')
    cards.append(f'<section><h2>{e(cat["name"])}</h2>{"".join(rows)}</section>')

page = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(SPEC['title'])} · tenpm.lab</title>
<style>
:root{{--bg:#fbf4ea;--ink:#3b2f2a;--sub:#8c7b70;--acc:#d9764f;--card:#fff;--line:#e9dccd}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}
main{{max-width:560px;margin:0 auto;padding:28px 18px 60px}}
.badge{{display:inline-block;background:var(--acc);color:#fff;border-radius:99px;padding:4px 12px;font-size:13px;font-weight:700}}
h1{{font-size:26px;margin:14px 0 8px}}.intro{{color:var(--sub);font-size:15px;line-height:1.55;margin:0 0 10px}}
.notice{{font-size:12px;color:var(--sub);background:#f3e8da;border-radius:12px;padding:10px 12px;line-height:1.5}}
h2{{font-size:17px;margin:26px 0 10px}}
.item{{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:8px 0;text-decoration:none;color:inherit}}
.item:active{{transform:scale(.99)}}.name{{font-weight:700;font-size:15px}}.say{{color:var(--sub);font-size:13px;margin-top:3px}}
.go{{color:var(--acc);font-weight:700;font-size:14px;white-space:nowrap}}
.tag{{font-size:11px;font-weight:700;color:var(--acc);border:1px solid var(--acc);border-radius:99px;padding:1px 7px;margin-left:6px;vertical-align:2px}}
.tag.soft{{color:var(--sub);border-color:var(--line)}}
footer{{margin-top:34px;font-size:12px;color:var(--sub);line-height:1.6}}
footer a{{color:var(--sub)}}
</style></head><body><main>
<span class="badge">tenpm.lab</span>
<h1>{e(SPEC['title'])}</h1>
<p class="intro">{e(SPEC['intro'])}</p>
<p class="notice">이 페이지의 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.<br>
'페이백'은 구매 후 리뷰 작성 대가로 구매 금액을 돌려받은 제품이에요. '비슷한 상품'은 우리가 산 게 품절이거나 물려받은 거라 비슷한 걸 걸어둔 거예요.</p>
{"".join(cards)}
<footer>매일 밤 10시 실험 기록 → 쓰레드 @tenpm.lab<br>
<a href="https://blog.naver.com/tenpmlab">블로그 · 텐피엠 퇴근 후 AI 부업</a></footer>
</main></body></html>"""
os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
open(os.path.join(HERE, "docs", "index.html"), "w", encoding="utf-8").write(page)
print("페이지 완성:", sum(len(c["items"]) for c in SPEC["cats"]), "개")
