# -*- coding: utf-8 -*-
"""
생필품 단위 가격 비교 특가 글 (쿠팡파트너스 공식 검색 API만 사용)
  python deal_unit.py sample        → posts/draft 에 샘플 2개
  python deal_unit.py 1230          → 오늘 12:30 queue 글 1개
쿠팡 검색 상위 상품들의 롤당·매당·L당 가격을 계산해서
'보통(중간값)보다 몇 % 싼지'를 첫 줄에 넣는다. 숫자는 전부 API 가격 그대로.
원본 응답·긴 링크(AF 코드)는 저장하지 않는다.
"""
import datetime, glob, json, os, re, statistics, sys, urllib.parse, urllib.request
from coupang_stats import BASE, call

HERE = os.path.dirname(os.path.abspath(__file__))
KST = datetime.timezone(datetime.timedelta(hours=9))
LOG = os.path.join(HERE, "posts", "deal_log.txt")

# 검색어: (단위, 단위 정규식, 단위 환산, 그럴듯한 단위가격 범위)
KW = {
    "휴지":       ("롤", r"(\d+)\s*롤", 1, (100, 5000)),
    "키친타월":   ("롤", r"(\d+)\s*롤", 1, (300, 6000)),
    "물티슈":     ("매", r"(\d+)\s*매", 1, (3, 100)),
    "생수":       ("L", r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|L|l)(?![a-zA-Z])", None, (80, 3000)),
    "세탁세제":   ("L", r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|L|l)(?![a-zA-Z])", None, (800, 40000)),
    "섬유유연제": ("L", r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|L|l)(?![a-zA-Z])", None, (800, 40000)),
    "주방세제":   ("L", r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|L|l)(?![a-zA-Z])", None, (800, 40000)),
    "기저귀":     ("매", r"(\d+)\s*매", 1, (50, 1500)),
    "핫팩":       ("개", r"(\d+)\s*개", 1, (100, 3000)),
    "건전지":     ("개", r"(\d+)\s*(?:개|입)", 1, (100, 3000)),
}
ORDER = list(KW)


def items(res):
    d = res.get("data") if isinstance(res, dict) else res
    if isinstance(d, dict):
        d = d.get("productData") or d.get("data") or []
    return d or []


def qty(name, kw):
    unit, pat, _, _ = KW[kw]
    m = re.search(pat, name)
    if not m:
        return None
    if unit == "L":
        v = float(m.group(1))
        base = v / 1000 if m.group(2).lower() == "ml" else v
        rest = name[m.end():]
        mult = 1
        mm = re.search(r"(?:[x×X\*]\s*(\d+))|(?:(\d+)\s*(?:개|병|팩|입|통|박스))", rest)
        if mm:
            mult = int(mm.group(1) or mm.group(2))
        return base * mult
    base = int(m.group(1))
    rest = name[m.end():]
    mult = 1
    if unit != "개":
        mm = re.search(r"(?:[x×X\*]\s*(\d+))|(?:(\d+)\s*(?:개|팩|박스|세트))", rest)
        if mm:
            mult = int(mm.group(1) or mm.group(2))
    return base * mult


def short(name):
    s = name.split(",")[0].strip()
    return s if len(s) <= 26 else s[:25] + "…"


def qty_text(q, unit):
    return (f"{q:g}L" if unit == "L" else f"{int(q)}{unit}")


def pick(kw):
    unit, _, _, (lo, hi) = KW[kw]
    got = items(call("GET", f"{BASE}/products/search",
                     "keyword=" + urllib.parse.quote(kw) + "&limit=10&subId=deal"))
    rows = []
    for it in got:
        name, price = str(it.get("productName", "")), it.get("productPrice")
        q = qty(name, kw)
        if not q or not price:
            continue
        up = price / q
        if lo <= up <= hi:
            rows.append({"pid": str(it["productId"]), "name": name, "price": int(price), "q": q,
                         "up": up, "img": it.get("productImage"), "rocket": it.get("isRocket")})
    best = None
    for c in sorted(rows, key=lambda r: r["up"]):
        others = [r for r in rows if r is not c and 0.5 <= r["q"] / c["q"] <= 2]
        if len(others) < 3:
            continue
        ref = statistics.median(r["up"] for r in others) * c["q"]
        pct = round((ref - c["price"]) / ref * 100)
        if 15 <= pct <= 60:
            best, med, n = c, ref, len(others)
            break
    if not best:
        return None, f"{kw}: 비슷한 양끼리 비교할 상품 부족/차이 작음"
    best.update(kw=kw, unit=unit, med=med, pct=pct, n=n)
    return best, "ok"


def won(x):
    return f"{round(x):,}" if x >= 10 else f"{x:.1f}"


def make_image(d, out):
    from PIL import Image, ImageDraw, ImageFont
    fonts = sorted(glob.glob("/usr/share/fonts/**/NotoSansCJK*Bl*.tt*", recursive=True)) + \
        sorted(glob.glob("/usr/share/fonts/**/NotoSansCJK*Bold*.tt*", recursive=True))
    F = fonts[0]
    req = urllib.request.Request(d["img"], headers={"User-Agent": "Mozilla/5.0"})
    tmp = out + ".src"
    with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as f:
        f.write(r.read())
    im = Image.open(tmp).convert("RGB").resize((1080, 1080))
    os.remove(tmp)
    dr = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(F, 120, index=1 if F.endswith("ttc") else 0)
    f2 = ImageFont.truetype(F, 50, index=1 if F.endswith("ttc") else 0)
    dr.ellipse((30, 30, 330, 330), fill="#e53935")
    dr.text((180, 180), f"-{d['pct']}%", font=f1 if d["pct"] < 100 else f2, fill="white", anchor="mm")
    dr.rectangle((0, 900, 1080, 1080), fill=(20, 20, 20))
    dr.text((540, 990), f"평균 {round(d['med']):,}원 → {d['price']:,}원",
            font=f2, fill="#ffd54f", anchor="mm")
    im.save(out, quality=90)


def link(pid, sub):
    res = call("POST", f"{BASE}/deeplink",
               body={"coupangUrls": [f"https://www.coupang.com/vp/products/{pid}"], "subId": sub})
    d = items(res)
    return d[0].get("shortenUrl") if d else None


def text(d, lk, photo, now, variant):
    u, p = d["unit"], d["pct"]
    p, nm = d["pct"], short(d["name"])
    first = [
        f"🔥 -{p}% {nm} 지금 {d['price']:,}원 (광고)",
        f"🚨 평균보다 {p}% 쌈! {nm} (광고)",
        f"⚡ {nm} 지금 -{p}% 가격 (광고)",
    ][variant % 3]
    body = [
        "주제: 특가",
        f"사진: {photo}",
        first,
        "",
        f"평균 {round(d['med']):,}원 → 지금 {d['price']:,}원 (-{p}%)",
        "",
        "지금! 지금! 지금!",
        "가격 언제 돌아갈지 모름",
        "어차피 사야 되는 거면 쌀 때 쟁여두기",
        "---",
        f"{nm} 👉 {lk}",
        f"※ {now:%m/%d %H:%M} 기준 쿠팡 가격. 평균은 쿠팡 검색 상위 비슷한 상품 {d['n']}개 같은 양 환산",
        "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
    ]
    return "\n".join(body) + "\n"


def used_recent():
    if not os.path.exists(LOG):
        return set()
    return {l.split("|")[2].strip() for l in open(LOG, encoding="utf-8").read().splitlines()[-20:] if l.count("|") >= 2}


def run(n, dest_dir, hhmm=None):
    now = datetime.datetime.now(KST)
    start = now.timetuple().tm_yday * 2 + (1 if hhmm and hhmm >= "1700" else 0)
    recent = used_recent()
    made, notes = 0, []
    for i in range(len(ORDER)):
        if made >= n:
            break
        kw = ORDER[(start + i) % len(ORDER)]
        try:
            d, why = pick(kw)
        except Exception as e:
            d, why = None, f"{kw}: {str(e)[:60]}"
        if not d or d["pid"] in recent:
            notes.append(why if not d else f"{kw}: 최근에 올린 상품")
            continue
        os.makedirs(os.path.join(HERE, "images", "deal"), exist_ok=True)
        photo = f"deal/{d['pid']}.jpg"
        make_image(d, os.path.join(HERE, "images", photo))
        lk = link(d["pid"], "dl" + now.strftime("%m%d") + d["pid"][-5:])
        if not lk:
            notes.append(f"{kw}: 링크 실패")
            continue
        stamp = now.strftime("%Y%m%d") + "-" + (hhmm or now.strftime("%H%M"))
        fn = os.path.join(dest_dir, f"{stamp}_deal_{made}.txt" if not hhmm else f"{stamp}_deal.txt")
        open(fn, "w", encoding="utf-8").write(text(d, lk, photo, now, start + made))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{now:%Y-%m-%d %H:%M} | {kw} | {d['pid']} | -{d['pct']}% | {os.path.basename(fn)}\n")
        made += 1
    print("made", made, notes)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if arg == "dump":
        dump([("하기스 기저귀", "기저귀"), ("하기스 기저귀 대용량", "기저귀"), ("팸퍼스 기저귀", "기저귀"),
              ("기저귀 소형 팩", "기저귀"), ("보솜이 기저귀", "기저귀")])
    elif arg == "sample":
        os.makedirs(os.path.join(HERE, "posts", "draft"), exist_ok=True)
        run(2, os.path.join(HERE, "posts", "draft"))
    else:
        run(1, os.path.join(HERE, "posts", "queue"), arg)


def dump(keywords):
    """검색 결과 이름·가격·수량만 curate/dump.json 에 (링크·코드 저장 안 함)"""
    out = {}
    for kw, unitkw in keywords:
        got = items(call("GET", f"{BASE}/products/search",
                         "keyword=" + urllib.parse.quote(kw) + "&limit=10&subId=dump"))
        out[kw] = [{"pid": str(it.get("productId")), "name": it.get("productName"),
                    "price": it.get("productPrice"), "rocket": it.get("isRocket"),
                    "q": qty(str(it.get("productName", "")), unitkw)} for it in got]
    json.dump(out, open(os.path.join(HERE, "curate", "dump.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
