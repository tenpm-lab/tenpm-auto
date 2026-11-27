# -*- coding: utf-8 -*-
"""
생필품 단위 가격 비교 특가 글 (쿠팡파트너스 공식 검색 API만 사용)
  python deal_unit.py sample        → posts/draft 에 샘플 2개
  python deal_unit.py 1230          → 오늘 12:30 queue 글 1개
쿠팡 검색 상위 상품들의 롤당·매당·L당 가격을 계산해서
'보통(중간값)보다 몇 % 싼지'를 첫 줄에 넣는다. 숫자는 전부 API 가격 그대로.
원본 응답·긴 링크(AF 코드)는 저장하지 않는다.
"""
import datetime, glob, json, os, re, statistics, sys, urllib.parse, urllib.request, zlib
LAST_NAME = ""
MORE = []  # save_image 가 고른 2·3번 사진 (다른 상품)
SHEET = None  # imgtest 때만 후보 사진 모음
VIDEO_ON = False  # 11/23 확대 영상 품질 별로 → 끔. 더 나은 영상 방식 정해지면 켜기
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
        lk = link(d["pid"], "ssageitem01")
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


BAD = ("업소용", "업소", "식당", "말통", "드럼", "대형마트용", "pallet")


def fetch_img(url):
    from PIL import Image
    import io
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def pretty(im):
    """0~1. 흰 배경이 적고(실사용 장면), 해상도가 크고, 색이 너무 단조롭지 않을수록 높음"""
    t = im.resize((120, 120))
    px = list(t.getdata())
    white = sum(1 for r, g, b in px if r > 240 and g > 240 and b > 240) / len(px)
    big = min(1.0, min(im.size) / 800)
    return round(0.5 + (1 - white) * 0.3 + big * 0.2, 3)


def text_words(im):
    """사진 속 글자 덩어리 수 (스펙표·광고 배너 거르기). tesseract 없으면 0"""
    import subprocess, tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            im.convert("L").resize((900, 900)).save(f.name)
            out = subprocess.run(["tesseract", f.name, "-", "-l", "kor+eng", "--psm", "11", "tsv"],
                                 capture_output=True, text=True, timeout=60).stdout.splitlines()[1:]
    except Exception:
        return 0
    n = 0
    for line in out:
        c = line.split("\t")
        if len(c) == 12 and len(c[11].strip()) >= 2 and float(c[10]) > 70:
            n += 1
    return n


def save_image(key, tag):
    """'싸게 사는 법' 글용 사진 + 그 상품 링크: 쿠팡 검색(품목 대용량) 상위 중 가정용 상품 하나.
    사진은 글자·가격 없이 정사각형으로 images/deal/<tag>.jpg. 반환 (사진경로, 상품 짧은 링크)"""
    try:
        from PIL import Image
        got = items(call("GET", f"{BASE}/products/search",
                         "keyword=" + urllib.parse.quote(key) + "&limit=10&subId=img"))
        ok = [x for x in got if x.get("productImage")
              and not any(b in str(x.get("productName", "")) for b in BAD)
              and not re.search(r"(1[5-9]|[2-9]\d)\s*L", str(x.get("productName", "")))]
        # 사진이 검색어랑 맞는 상품인지: 검색어 낱말이 상품명에 가장 많이 든 것 (11/23 '노트북 확장 모니터' → 일반 노트북 사진 사고)
        toks = [t for t in re.split(r"\s+", key) if len(t) >= 2 and t not in ("대용량", "추천", "가정용")]
        def score(x):
            nm = str(x.get("productName", "")).replace(" ", "")
            return sum(t.replace(" ", "") in nm for t in toks)
        need = min(2, len(toks))
        # 숫자 든 낱말(3화면, 2구, 10m 등)은 꼭 맞아야 함 (11/23 '3화면' 검색에 일반 모니터 사진 걸림)
        SYN = {"3화면": ("3화면", "트리플", "3면"), "2화면": ("2화면", "듀얼", "2면")}
        must = [t for t in toks if re.search(r"\d", t)]
        def has_must(x):
            nm = str(x.get("productName", "")).replace(" ", "")
            return all(any(a in nm for a in SYN.get(t, (t,))) for t in must)
        cands = sorted([x for x in ok if score(x) >= need and has_must(x)], key=score, reverse=True)
        if not cands:
            print("검색어와 맞는 상품 없음", key, ok and ok[0].get("productName"))
            return None, None
        # 예쁜 사진 고르기 (11/23 Ssuii: "불러올때 이쁜 사진을 좀 불러오자"):
        # 검색어가 맞는 상품들 사진을 다 받아서, 흰 배경 단독컷보다 실제 쓰는 장면(배경 있는 사진)을 우선
        best = None
        scored = []
        for x in cands[:8]:
            try:
                im = fetch_img(x["productImage"])
            except Exception:
                continue
            pr = pretty(im)
            tw = text_words(im)
            pr = round(pr - (0.6 if tw >= 4 else 0.15 if tw >= 2 else 0), 3)  # 글자 많은 배너·스펙표는 감점
            x["_pretty"] = pr
            x["_rank"] = pr + 0.25 * (score(x) - need)  # 검색어가 더 많이 맞으면 조금 가산
            scored.append((x, im))
            if best is None or x["_rank"] > best[0]["_rank"]:
                best = (x, im, pr)
            if SHEET is not None:
                SHEET.append((im, f'{pr:.2f} / {score(x)}'))
        if not best:
            return None, None
        it, im, _ = best
        global LAST_NAME
        LAST_NAME = str(it.get("productName", ""))
        os.makedirs(os.path.join(HERE, "images", "deal"), exist_ok=True)
        tag = f"{tag}_{it['productId']}"
        out = os.path.join(HERE, "images", "deal", tag + ".jpg")
        w, h = im.size
        side = max(w, h)
        bg = Image.new("RGB", (side, side), "white")
        bg.paste(im, ((side - w) // 2, (side - h) // 2))
        bg.resize((1080, 1080)).save(out, quality=90)
        # 괜찮은 사진 여러 장 (11/23 Ssuii: "괜찮은 사진 여러장을 넣어도 되지않아? 독자들이 보고 판단할 수 있게")
        # 1등 말고도 점수 0.45 이상인 다른 상품 최대 2개 → 넘겨보기 2·3번. 사진마다 자기 상품 링크
        MORE.clear()
        rest = sorted([z for z in scored if z[0] is not it and z[0]["_pretty"] >= 0.75], key=lambda z: -z[0]["_rank"])
        seen = {str(it.get("productName", ""))[:15]}
        uniq = []
        for z in rest:  # 이름이 같은 상품(색상만 다른 것)은 한 번만
            nm = str(z[0].get("productName", ""))[:15]
            if nm not in seen:
                seen.add(nm)
                uniq.append(z)
        for j, (x, xim) in enumerate(uniq[:2], start=2):
            w, h = xim.size
            side = max(w, h)
            bg = Image.new("RGB", (side, side), "white")
            bg.paste(xim, ((side - w) // 2, (side - h) // 2))
            bg.resize((1080, 1080)).save(os.path.join(HERE, "images", "deal", f"{tag}_{j}.jpg"), quality=90)
            MORE.append({"image": f"deal/{tag}_{j}.jpg", "item_link": link(str(x["productId"]), "ssagesave01"),
                         "item_name": str(x.get("productName", ""))[:60]})
        return f"deal/{tag}.jpg", link(str(it["productId"]), "ssagesave01")
    except Exception as e:
        print("사진 실패", key, str(e)[:80])
        return None, None


def links():
    """deal/links.txt 의 '이름|쿠팡주소' 줄마다 짧은 파트너 링크를 만들어 curate/links.json 에 (긴 링크·코드 저장 안 함)"""
    now = datetime.datetime.now(KST)
    out = {}
    for n, line in enumerate(open(os.path.join(HERE, "deal", "links.txt"), encoding="utf-8").read().splitlines()):
        if "|" not in line:
            continue
        key, url = [x.strip() for x in line.split("|", 1)]
        try:
            res = call("POST", f"{BASE}/deeplink", body={"coupangUrls": [url], "subId": "ssagesave01"})
            d = items(res)
            out[key] = {"link": d[0].get("shortenUrl") if d else None, "subId": "ssagesave01"}
            img, item = save_image(key, f"sv{now:%m%d}_{zlib.crc32(key.encode()) % 100000:05d}")
            if img:
                out[key]["image"] = img
                out[key]["item_name"] = LAST_NAME[:60]  # 글 쓸 때 상품이 맞는지 보라고
                # 사진 1장 vs 영상+사진 넘겨보기 실험 (11/23): 두 번째 키마다 "영상, 사진" 2장 묶음. 글의 '사진:' 줄에 그대로 쓰면 됨
                if VIDEO_ON and n % 2 == 1:
                    vid = make_video(img)
                    if vid:
                        out[key]["photo"] = img
                        out[key]["image"] = f"{vid}, {img}"
            if item:
                out[key]["item_link"] = item
            if img and MORE:
                # 넘겨보기용: images 를 '사진:' 줄에 그대로, 이어 쓰기에 1번·2번·3번 링크를 순서대로
                out[key]["more"] = list(MORE)
                out[key]["images"] = ", ".join([img] + [m["image"] for m in MORE])
        except Exception as e:
            out[key] = {"error": str(e)[:80]}
    made(out.values())
    # 글 쓰는 Claude(주간 점검)가 보는 안내. 프롬프트를 안 고쳐도 여기서 읽힘
    out["_글쓰기_안내"] = ("images 가 있으면 '사진:' 줄에 images 를 그대로 (넘겨보기). 본문은 '넘겨서 골라봐' 식으로 비교, "
                       "이어 쓰기에 '1번 👉 item_link', '2번 👉 more[0].item_link', '3번 👉 more[1].item_link' 순서대로. "
                       "사진 순서 = 번호 순서. 각 상품 이름은 item_name 으로 확인해서 사실만 쓸 것. images 없으면 image 1장 + item_link.")
    json.dump(out, open(os.path.join(HERE, "curate", "links.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def make_video(img):
    """상품 사진 → 6초 천천히 다가가는 영상 (1080x1080, 무음 오디오 포함). 반환 'deal/xxx.mp4'"""
    import subprocess
    src = os.path.join(HERE, "images", img)
    dst = src.rsplit(".", 1)[0] + ".mp4"
    vf = ("scale=1440:1440,zoompan=z='min(zoom+0.0006,1.10)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          ":s=1080x1080:fps=30,format=yuv420p")
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", src, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-vf", vf, "-t", "6", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "64k",
                        "-shortest", "-movflags", "+faststart", dst], check=True, timeout=120)
        return img.rsplit(".", 1)[0] + ".mp4"
    except Exception as e:
        print("영상 실패", str(e)[:80])
        return None


def made(vals):
    """만든 쿠팡 링크 장부 (daily_check.py 가 '등록 채널로 만든 링크'인지 볼 때 씀)"""
    f = os.path.join(HERE, "stats", "links_made.csv")
    new = not os.path.exists(f)
    with open(f, "a", encoding="utf-8") as w:
        if new:
            w.write("만든날,subId,링크\n")
        for v in vals:
            for k in ("link", "item_link"):
                if v.get(k):
                    w.write(f"{datetime.date.today():%Y%m%d},{v.get('subId', '')},{v[k]}\n")
            for m in v.get("more", []):
                if m.get("item_link"):
                    w.write(f"{datetime.date.today():%Y%m%d},{v.get('subId', '')},{m['item_link']}\n")


def goldbox():
    """골드박스 테스트: 할인율·원래 가격이 오는지 필드만 확인 (주소·코드는 저장 안 함)"""
    res = call("GET", f"{BASE}/products/goldbox", "subId=ssageitem01&imageSize=512x512")
    data = res.get("data") or []
    if isinstance(data, dict):
        data = data.get("productData") or []
    out = {"count": len(data), "keys": sorted(set(k for d in data for k in d)) if data else [], "rCode": res.get("rCode"), "rMessage": res.get("rMessage"),
           "sample": [{k: v for k, v in d.items() if "url" not in k.lower() and "image" not in k.lower() and "tracking" not in k.lower()} for d in data[:8]]}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curate", "goldbox.json"), "w"), ensure_ascii=False, indent=1)
    print("골드박스", out["count"], out["keys"])


GOLD_OK = ("생활용품", "식품", "뷰티", "출산", "유아", "주방", "반려", "세제", "헬스")
# 종류별 "그 사람의 순간" 첫 줄 (11/23 Ssuii가 ④ 콕 집어 부르기 고름, ① 가격 맞히기와 번갈아 실험)
GOLD_HOOK = [
    (("화장지", "휴지", "물티슈", "키친타월"), "{n} 떨어질 때마다 급하게 사는 사람 손 🙋"),
    (("세제", "유연제", "세탁"), "빨래할 때마다 {n} 얼마 남았나 보는 사람 손 🙋"),
    (("식품", "음료", "커피", "두유", "콜라", "생수"), "냉장고에 {n} 떨어지면 불안한 사람 손 🙋"),
    (("뷰티", "로션", "크림", "샴푸", "바디"), "겨울마다 {n} 통째로 바르는 사람 손 🙋"),
    (("출산", "유아", "기저귀", "분유"), "{n} 한 달에 몇 통씩 쓰는 집 손 🙋"),
]


def gold_photo(d, tag):
    try:
        from PIL import Image
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "deal", f"{tag}.jpg")
        req = urllib.request.Request(d["productImage"], headers={"User-Agent": "Mozilla/5.0"})
        open(out + ".src", "wb").write(urllib.request.urlopen(req, timeout=20).read())
        im = Image.open(out + ".src").convert("RGB")
        side = max(im.size)
        bg = Image.new("RGB", (side, side), "white")
        bg.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2))
        bg.resize((1080, 1080)).save(out, quality=90)
        return f"deal/{tag}.jpg"
    except Exception as e:
        print("사진 실패", e)
        return None


def goldpost():
    """부계정 '오늘의 골드박스' 글 (매일 아침 자동, 09:00). 할인율은 API에 없어서 안 씀.
    형식은 날짜 홀짝으로 번갈아: 짝수 = ④ 콕 집어 부르기 / 홀수 = ① 가격 맞히기. 일요일 리포트에서 클릭 비교."""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posts", "deal", "queue")
    fmt = "call" if now.day % 2 == 0 else "price"
    fn = os.path.join(q, f"{now:%Y%m%d}-0900_gold_{fmt}.txt")
    test = os.environ.get("GOLD_TEST")  # 테스트: 두 형식 모두 curate/ 에만 써봄
    if test:
        fmt = test
        fn = os.path.join(os.path.dirname(q), "..", "..", "curate", f"gold_test_{fmt}.txt")
    elif glob.glob(os.path.join(q, f"{now:%Y%m%d}-0900_gold*")) or glob.glob(os.path.join(os.path.dirname(q), "done", f"{now:%Y%m%d}-0900_gold*")):
        print("이미 있음"); return
    elif f"{now:%Y%m%d}" < "20261126":  # 부계정 워밍업(링크 없이) 기간
        print("워밍업 기간 - 쉼"); return
    res = call("GET", f"{BASE}/products/goldbox", "subId=ssageitem01&imageSize=512x512")
    data = res.get("data") or []
    pick = [d for d in data if any(k in (d.get("categoryName") or "") for k in GOLD_OK)]
    pick = (pick + [d for d in data if d not in pick])[:3]
    if len(pick) < 3:
        print("골드박스 상품 부족", len(data)); return
    rows = []
    for d in pick:
        lk = link(str(d["productId"]), "ssageitem01")
        if not lk:
            print("링크 실패"); return
        rows.append((short(d["productName"]), lk, d))
        made([{"link": lk, "subId": "ssageitem01"}])
    top_nm, top_lk, top = rows[0]
    word = top_nm.split()[0] if fmt == "call" else top_nm
    hay = top_nm + " " + (top.get("categoryName") or "")
    hook = next((h for keys, h in GOLD_HOOK if any(k in hay for k in keys)), "{n} 쟁여두는 사람 손 🙋")
    photo = gold_photo(top, f"gold_{now:%Y%m%d}")
    body = ["주제: 생활꿀템"] + ([f"사진: {photo}"] if photo else [])
    if fmt == "call":
        body += [hook.format(n=word) + " (광고)", "", "오늘 쿠팡 하루 특가에 떴음", "내일 아침이면 목록에서 빠짐", "", "같이 뜬 생필품 2개 더 있음 👀", "---",
                 f"{top_nm}", f"👉 {top_lk}", ""]
    else:
        body += [f"이거 오늘 얼마일 것 같아? (광고)", "", f"{top_nm}", "", "생각한 가격 하나 정하고 이어쓰기 열어보기 👀", "---",
                 f"정답: {int(top['productPrice']):,}원", f"(오늘 아침 쿠팡 골드박스 기준, 내일이면 바뀜)", f"👉 {top_lk}", ""]
    body += ["같이 뜬 거"]
    for nm, lk, _ in rows[1:]:
        body += [f"· {nm}", f"👉 {lk}"]
    body += ["", "가격은 링크에서 꼭 확인!", "", "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."]
    open(fn, "w").write("\n".join(body) + "\n")
    print("골드박스 글", fmt, fn, [r[0] for r in rows])


# ---------- TOP 5 목록 글 (11/28 Ssuii: "쿠팡에서 제일 인기많은것 후기좋은것 이런식으러 해서 사람을 끌어모아보자") ----------
# deal/top5.txt 한 줄에 하나: "YYYYMMDD-HHMM|검색어|보여줄 이름|주제"  예) 20261128-2200|과자|과자|간식추천
# 순위 = 쿠팡 검색 상위 순서 그대로 (API 에 리뷰 수·별점은 없음 → 글에 기준을 밝힘). 같은 상품 맛·용량 다른 건 하나만.
def _font(size):
    from PIL import ImageFont
    F = (sorted(glob.glob("/usr/share/fonts/**/NotoSansCJK*Bl*.tt*", recursive=True)) +
         sorted(glob.glob("/usr/share/fonts/**/NotoSansCJK*Bold*.tt*", recursive=True)) +
         sorted(glob.glob("/usr/share/fonts/**/*CJK*Bold*.tt*", recursive=True)))[0]
    return ImageFont.truetype(F, size, index=1 if F.endswith("ttc") else 0)


def _square(url):
    from PIL import Image
    import io
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=20).read())).convert("RGB")
    side = max(im.size)
    bg = Image.new("RGB", (side, side), "white")
    bg.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2))
    return bg.resize((1080, 1080))


def _badge(im, n, size=1080):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    r = size // 7
    d.ellipse((size // 30, size // 30, size // 30 + r, size // 30 + r), fill="#e53935")
    d.text((size // 30 + r // 2, size // 30 + r // 2), f"{n}위", font=_font(r // 3), fill="white", anchor="mm")
    return im


# 여러 상품 묶은 세트는 순위 글에 안 맞음 (11/28 첫 시도: '과자' 상위가 사무실 과자 세트뿐)
SET_RE = re.compile(r"세트|\d+\s*종|혼합|모음|골라|랜덤|\+|선물")


MAKERS = ("농심", "오뚜기", "팔도", "삼양", "오리온", "롯데", "롯데웰푸드", "해태", "해태제과", "크라운", "빙그레",
          "동원", "CJ", "풀무원", "하림", "청정원", "대상", "남양", "매일", "동서", "맥심", "노브랜드", "곰곰", "탐사")


def _brand_key(name):
    """같은 상품(제조사 이름 유무·용량만 다른 것)을 하나로 보기 위한 열쇠: 제조사·괄호 뺀 첫 낱말"""
    w = [t for t in re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", name).replace(",", " ").split() if t not in MAKERS]
    return w[0] if w else name


def _multi_maker(name):
    return sum(1 for m in ("농심", "오뚜기", "팔도", "삼양", "오리온", "롯데", "해태", "크라운") if m in name) >= 2


def top5_one(stamp, kw, label, topic):
    from PIL import Image, ImageDraw
    q = os.path.join(HERE, "posts", "deal", "queue")
    tag = f"top5_{stamp.replace('-', '')}"
    fn = os.path.join(q, f"{stamp}_top5_{tag[-6:]}.txt")
    if glob.glob(os.path.join(q, f"{stamp}_*")) or glob.glob(os.path.join(HERE, "posts", "deal", "done", f"{stamp}_*")):
        print("그 자리에 이미 글 있음", stamp); return
    got = []
    for qkw in (kw, kw + " 베스트"):  # 세트 상품을 빼고 5개가 안 되면 한 번 더 찾음
        got += items(call("GET", f"{BASE}/products/search", "keyword=" + urllib.parse.quote(qkw) + "&limit=10&subId=ssageitem01"))
        if sum(1 for x in got if not SET_RE.search(str(x.get("productName", "")))) >= 7:
            break
    rows, seen = [], set()
    for x in got:
        nm = str(x.get("productName", ""))
        if not x.get("productImage") or any(b in nm for b in BAD) or SET_RE.search(nm) or _multi_maker(nm):
            continue
        k = _brand_key(nm)
        if k in seen:
            continue
        seen.add(k)
        rows.append(x)
        if len(rows) == 5:
            break
    if len(rows) < 5:
        print("상품 부족", kw, len(rows)); return
    photos, lines, links_ = [], [], []
    tiles = []
    for i, x in enumerate(rows, 1):
        lk = link(str(x["productId"]), "ssageitem01")
        if not lk:
            print("링크 실패"); return
        made([{"link": lk, "subId": "ssageitem01"}])
        im = _square(x["productImage"])
        tiles.append(im.copy())
        _badge(im, i).save(os.path.join(HERE, "images", "deal", f"{tag}_{i}.jpg"), quality=90)
        photos.append(f"deal/{tag}_{i}.jpg")
        nm = short(str(x["productName"]))
        lines.append(f"{i}위 {nm}")
        links_.append(f"{i}위 👉 {lk}")
    # 표지: 왼쪽 위 제목 칸 + 상품 5칸 (3x2)
    cover = Image.new("RGB", (1080, 720), "white")
    t = 360
    d = ImageDraw.Draw(cover)
    d.rectangle((0, 0, t, t), fill=(24, 24, 24))
    d.text((t // 2, t // 2 - 50), "쿠팡", font=_font(44), fill="#ffd54f", anchor="mm")
    d.text((t // 2, t // 2 + 10), label, font=_font(64 if len(label) <= 4 else 44), fill="white", anchor="mm")
    d.text((t // 2, t // 2 + 85), "TOP 5", font=_font(60), fill="#ffd54f", anchor="mm")
    for i, im in enumerate(tiles):
        pos = i + 1
        x0, y0 = (pos % 3) * t, (pos // 3) * t
        cover.paste(_badge(im.resize((t, t)), i + 1, t), (x0, y0))
    cover.save(os.path.join(HERE, "images", "deal", f"{tag}_0.jpg"), quality=90)
    photos.insert(0, f"deal/{tag}_0.jpg")
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    body = [f"주제: {topic}", "사진: " + ", ".join(photos),
            f"쿠팡 {label} TOP 5 (광고)",
            "(이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.)", ""]
    body += lines
    body += ["", "넘겨서 하나씩 봐봐", "몇 개나 먹어봄?" if topic in ("간식추천", "먹거리") else "몇 개나 써봄?",
             "---"] + links_ + ["", f"쿠팡에서 '{kw}' 검색했을 때 맨 위 5개 ({now:%m/%d} 기준, 같은 상품 맛·용량 다른 건 하나만)",
             "가격·후기는 링크에서 확인!", "", "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."]
    open(fn, "w", encoding="utf-8").write("\n".join(body) + "\n")
    with open(LOG, "a", encoding="utf-8") as w:
        w.write(f"{now:%Y-%m-%d} | top5 | {kw} | ssageitem01 | {os.path.basename(fn)}\n")
    print("TOP5 글", fn, lines)


def top5():
    src = os.path.join(HERE, "deal", "top5.txt")
    for l in open(src, encoding="utf-8"):
        if l.count("|") >= 3 and not l.startswith("#"):
            stamp, kw, label, topic = [v.strip() for v in l.split("|")[:4]]
            try:
                top5_one(stamp, kw, label, topic)
            except Exception as e:
                print("실패", kw, e)
    open(src, "w", encoding="utf-8").write("# 형식: YYYYMMDD-HHMM|검색어|보여줄 이름|주제 (처리되면 비워짐)\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "top5":
        top5(); sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "goldpost":
        goldpost(); sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "goldbox":
        goldbox(); sys.exit()
    arg = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if arg == "links":
        links()
    elif arg == "imgtest":
        # deal/links.txt 키마다 후보 사진 모음판 → curate/imgtest_N.jpg (링크는 안 만듦)
        from PIL import Image, ImageDraw
        keys = [l.split("|")[0].strip() for l in open(os.path.join(HERE, "deal", "links.txt"), encoding="utf-8") if "|" in l]
        os.makedirs(os.path.join(HERE, "curate"), exist_ok=True)
        global_link = link
        link = lambda *a, **k: None  # noqa: E731  테스트라 파트너 링크는 안 만듦
        for i, k in enumerate(keys):
            SHEET = []
            img, _ = save_image(k, f"test_{i}")
            sheet = Image.new("RGB", (4 * 300, 2 * 330), "white")
            d = ImageDraw.Draw(sheet)
            for j, (im, lab) in enumerate(SHEET[:8]):
                sheet.paste(im.resize((290, 290)), ((j % 4) * 300 + 5, (j // 4) * 330 + 5))
                d.text(((j % 4) * 300 + 10, (j // 4) * 330 + 300), lab, fill="black")
            sheet.save(os.path.join(HERE, "curate", f"imgtest_{i}.jpg"), quality=85)
            print(k, "→", img, LAST_NAME[:40])
    elif arg == "dump":
        dump([("하기스 기저귀", "기저귀"), ("하기스 기저귀 대용량", "기저귀"), ("팸퍼스 기저귀", "기저귀"),
              ("기저귀 소형 팩", "기저귀"), ("보솜이 기저귀", "기저귀")])
    elif arg == "sample":
        os.makedirs(os.path.join(HERE, "posts", "draft"), exist_ok=True)
        run(2, os.path.join(HERE, "posts", "draft"))
    else:
        run(1, os.path.join(HERE, "posts", "queue"), arg)
