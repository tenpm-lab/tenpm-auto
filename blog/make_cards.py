# -*- coding: utf-8 -*-
"""
정보 글 블로그용 그림 틀 (따뜻한 크림 톤, 1080x1080). JSON 하나로 여러 장을 만든다.
  python blog/make_cards.py spec.json
spec.json 예:
{"prefix": "blog/thumbs/i_flu", "source": "출처 질병관리청",
 "cards": [
  {"type": "cover", "label": "육아 정보", "lines": ["애기 독감", "무료 접종 정리"], "sub": "6개월~14세, 4월 30일까지"},
  {"type": "steps", "kicker": "10분이면 끝", "title": "접종 받는 순서", "items": [["병원 찾기", "예방접종도우미에서 검색"], ["예약", "전화로 백신 있는지 확인"]]},
  {"type": "table", "kicker": "한눈에", "title": "대상과 기간", "rows": [["대상", "6개월~14세"], ["기간", "~2027.4.30"]]},
  {"type": "bars", "kicker": "...", "title": "...", "bars": [["신용카드", 15, "15%"], ["체크카드", 30, "30%"]], "note": "한 줄 설명"},
  {"type": "compare", "kicker": "...", "title": "...", "question": "처음 맞음?", "left": ["예", "2회 접종", ["4주 간격"]], "right": ["아니오", "1회 접종", ["매년 1번"]]},
  {"type": "checklist", "kicker": "정리", "title": "이것만 챙기기", "items": ["산모수첩·아기수첩 챙기기", "열 있으면 다음에"]}
 ]}
파일: prefix_1.jpg, prefix_2.jpg ... (cover는 prefix.jpg)
글자가 넘치면 자동으로 글씨를 줄인다.
"""
import json
import sys
from PIL import Image, ImageDraw, ImageFont

B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BG, INK, SUB, ACC, SOFT, LINE, MINT = "#fbf4ea", "#3b2f2a", "#8c7b70", "#d9764f", "#f6dfc8", "#e9dccd", "#e6efe1"
W = 1080
CARD, ONACC, QBG, QTXT, ALT, FOOT = "#fff", "#fff", INK, "#fff", "#b9a48f", "#a8968a"
DOT, BARS = "#f2a98a", ["#e9cdb6", "#f2a98a", "#d9764f", "#b85c38"]
# 시리즈 색 (spec 에 "palette": "threads" 등). 기본은 크림 톤(4. 생활정보)
# stock=주식, realestate=부동산, gov=정부지원사업, threads=쓰레드 가이드, affiliate=제휴 프로그램
PALETTES = {
    # 정보성 자료 > 2. 주식 (짙은 남색 + 빨강)
    "stock": dict(BG="#0f1622", INK="#ffffff", SUB="#a9b4c4", ACC="#ff6b6b", SOFT="#1f2a3a", LINE="#2c3a4e", MINT="#18212f",
                  CARD="#182231", ONACC="#0f1622", QBG="#ff6b6b", QTXT="#0f1622", ALT="#8592a5", FOOT="#8592a5",
                  DOT="#ff6b6b", BARS=["#3a4a60", "#7a5560", "#ff8f8f", "#ff6b6b"]),
    # 정보성 자료 > 3. 부동산 (짙은 청록 + 민트)
    "realestate": dict(BG="#0f1d1c", INK="#ffffff", SUB="#a6c2bd", ACC="#3fd0b6", SOFT="#1d3330", LINE="#29433f", MINT="#162926",
                       CARD="#162826", ONACC="#0f1d1c", QBG="#3fd0b6", QTXT="#0f1d1c", ALT="#7fa39d", FOOT="#7fa39d",
                       DOT="#3fd0b6", BARS=["#2c4a46", "#3f7f73", "#36b39c", "#3fd0b6"]),
    # 정보성 자료 > 1. 정부지원사업 (밝은 하늘 + 파랑)
    "gov": dict(BG="#eef4fb", INK="#1f2d3d", SUB="#6b7c8f", ACC="#2f74c0", SOFT="#d6e6f7", LINE="#d5dfeb", MINT="#e3f0e8",
                CARD="#ffffff", ONACC="#ffffff", QBG="#1f2d3d", QTXT="#ffffff", ALT="#8fa0b3", FOOT="#8a9aac",
                DOT="#2f74c0", BARS=["#c9dcf2", "#8fb8e6", "#2f74c0", "#1f5490"]),
    "affiliate": dict(BG="#1d1512", INK="#ffffff", SUB="#c4b0a6", ACC="#ff8a5b", SOFT="#3a2a24", LINE="#4a3830", MINT="#2a1f1b",
                      CARD="#2a1f1b", ONACC="#1d1512", QBG="#ff8a5b", QTXT="#1d1512", ALT="#a8968a", FOOT="#a8968a"),
    "threads": dict(BG="#17121f", INK="#ffffff", SUB="#b3aac4", ACC="#b69cff", SOFT="#2c2438", LINE="#3a3048", MINT="#241c30",
                    CARD="#221a2e", ONACC="#17121f", QBG="#b69cff", QTXT="#17121f", ALT="#8f86a3", FOOT="#8f86a3"),
}


def F(p, s):
    return ImageFont.truetype(p, s, index=1)


def fit(d, text, path, size, maxw):
    while size > 20 and d.textlength(text, font=F(path, size)) > maxw:
        size -= 2
    return F(path, size)


def base(kicker, title, source):
    im = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(im)
    d.text((80, 80), kicker, font=fit(d, kicker, R, 38, 920), fill=SUB)
    d.text((80, 135), title, font=fit(d, title, B, 64, 920), fill=INK)
    d.text((80, 1000), f"tenpm.lab · {source}", font=F(R, 28), fill=FOOT)
    return im, d


def cover(c, src):
    im = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(im)
    d.ellipse((W - 330, -120, W + 120, 330), fill=SOFT)
    d.ellipse((-160, W - 300, 260, W + 120), fill=MINT)
    d.ellipse((W - 210, 120, W - 150, 180), fill=DOT)
    lab = c.get("label", "생활 정보")
    d.rounded_rectangle((90, 130, 90 + d.textlength(lab, font=F(R, 40)) + 56, 200), radius=35, fill=DOT)
    d.text((118, 138), lab, font=F(R, 40), fill="#fff")
    y = 330
    lines = c["lines"]
    for i, t in enumerate(lines):
        d.text((90, y), t, font=fit(d, t, B, 92, 900), fill=INK if i < len(lines) - 1 else ACC)
        y += 125
    d.text((90, y + 30), c.get("sub", ""), font=fit(d, c.get("sub", ""), R, 42, 900), fill=SUB)
    d.text((90, W - 130), "tenpm.lab · " + c.get("foot", "생활 정보"), font=F(R, 36), fill=FOOT)
    return im


def steps(c, src):
    im, d = base(c.get("kicker", ""), c["title"], src)
    items = c["items"][:5]
    h = min(150, int(680 / len(items)) - 30)
    y = 270
    for i, (t, s) in enumerate(items):
        d.rounded_rectangle((80, y, 1000, y + h), radius=28, fill=CARD, outline=LINE, width=3)
        cy = y + h // 2
        d.ellipse((110, cy - 35, 180, cy + 35), fill=ACC)
        d.text((145, cy), str(i + 1), font=F(B, 40), fill=ONACC, anchor="mm")
        d.text((210, y + h * 0.15), t, font=fit(d, t, B, 44, 760), fill=INK)
        d.text((210, y + h * 0.58), s, font=fit(d, s, R, 30, 760), fill=SUB)
        if i < len(items) - 1:
            d.polygon([(530, y + h + 8), (570, y + h + 8), (550, y + h + 26)], fill=ACC)
        y += h + 34
    return im


def table(c, src):
    im, d = base(c.get("kicker", ""), c["title"], src)
    rows = c["rows"][:7]
    h = min(110, int(660 / len(rows)))
    d.rounded_rectangle((80, 270, 1000, 270 + h * len(rows) + 20), radius=28, fill=CARD, outline=LINE, width=3)
    y = 285
    for i, (a, b) in enumerate(rows):
        d.text((120, y + h / 2), a, font=fit(d, a, R, 38, 360), fill=SUB, anchor="lm")
        d.text((960, y + h / 2), b, font=fit(d, b, B, 40, 520), fill=ACC, anchor="rm")
        if i < len(rows) - 1:
            d.line((120, y + h, 960, y + h), fill=LINE, width=2)
        y += h
    return im


def bars(c, src):
    im, d = base(c.get("kicker", ""), c["title"], src)
    items = c["bars"][:4]
    mx = max(v for _, v, _ in items) or 1
    y = 290
    cols = BARS
    for i, (name, v, lab) in enumerate(items):
        d.text((80, y), name, font=fit(d, name, B, 44, 900), fill=INK)
        w = int(760 * v / mx)
        d.rounded_rectangle((80, y + 66, 80 + max(w, 40), y + 140), radius=20, fill=cols[i % 4])
        d.text((80 + max(w, 40) + 24, y + 76), lab, font=F(B, 48), fill=INK)
        y += 175
    if c.get("note"):
        d.text((80, 915), c["note"], font=fit(d, c["note"], R, 36, 920), fill=INK)
    return im


def compare(c, src):
    im, d = base(c.get("kicker", ""), c["title"], src)
    q = c["question"]
    d.rounded_rectangle((200, 290, 880, 400), radius=30, fill=QBG)
    d.text((540, 345), q, font=fit(d, q, B, 44, 640), fill=QTXT, anchor="mm")
    for cx, (lab, title, lines), col in [(300, c["left"], ACC), (780, c["right"], ALT)]:
        d.line((540, 400, cx, 520), fill=col, width=6)
        d.text((cx, 470), lab, font=F(B, 36), fill=col, anchor="mm")
        d.rounded_rectangle((cx - 230, 530, cx + 230, 880), radius=30, fill=CARD, outline=col, width=5)
        d.text((cx, 600), title, font=fit(d, title, B, 40, 420), fill=INK, anchor="mm")
        for i, l in enumerate(lines[:3]):
            d.text((cx, 690 + i * 64), l, font=fit(d, l, R, 34, 420), fill=SUB, anchor="mm")
    if c.get("note"):
        d.text((80, 920), c["note"], font=fit(d, c["note"], R, 32, 920), fill=SUB)
    return im


def checklist(c, src):
    im, d = base(c.get("kicker", ""), c["title"], src)
    items = c["items"][:6]
    y = max(280, int((W + 120 - len(items) * 118) / 2))
    for t in items:
        d.rounded_rectangle((80, y, 1000, y + 100), radius=24, fill=CARD, outline=LINE, width=3)
        d.rounded_rectangle((110, y + 28, 154, y + 72), radius=10, fill=ACC)
        d.text((132, y + 50), "✓", font=F(B, 32), fill=ONACC, anchor="mm")
        d.text((180, y + 50), t, font=fit(d, t, B, 38, 790), fill=INK, anchor="lm")
        y += 118
    return im


KINDS = {"cover": cover, "steps": steps, "table": table, "bars": bars, "compare": compare, "checklist": checklist}


def main(path):
    spec = json.load(open(path, encoding="utf-8"))
    if "palette" not in spec:  # 표지 라벨로 카테고리 색 자동 선택
        lab = next((c.get("label", "") for c in spec.get("cards", []) if c.get("type") == "cover"), "")
        for key, pal in (("주식", "stock"), ("부동산", "realestate"), ("정부지원", "gov")):
            if key in lab:
                spec["palette"] = pal
    if spec.get("palette") in PALETTES:
        globals().update(PALETTES[spec["palette"]])
    src = spec.get("source", "출처 확인")
    n, out = 0, []
    for c in spec["cards"]:
        im = KINDS[c["type"]](c, src)
        if c["type"] == "cover":
            fn = spec["prefix"] + ".jpg"
        else:
            n += 1
            fn = f"{spec['prefix']}_{n}.jpg"
        im.save(fn, quality=92)
        out.append(fn)
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
