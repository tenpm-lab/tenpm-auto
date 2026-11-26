# -*- coding: utf-8 -*-
"""
블로그 대표 이미지 (시리즈마다 색이 다름)
  python blog/make_thumb.py 출력.jpg "라벨" "윗줄|아랫줄" "부제" [시리즈]
시리즈: ai(AI 무료 활용 가이드, 하늘색) / coupang(쿠팡파트너스 가이드) / affiliate(제휴 프로그램 가이드, 코랄) / threads(쓰레드 가이드) / desk(직장인템 가이드) / ep(AI가 시키는 대로 연재)
시리즈를 안 주면 라벨 글자로 알아서 고름. 일상·생활 정보는 make_thumb_life.py / make_cards.py (크림 톤)
"""
import sys
from PIL import Image, ImageDraw, ImageFont

B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

SERIES = {
    # 배경, 강조색, 라벨 글자색, 큰 글씨, 부제, 선, 시계 테두리, 맨 아래 문구
    "coupang": dict(bg="#12141b", acc="#f5c400", lab_txt="#12141b", ink="#ffffff", sub="#aab0bd", line="#2a2e3a", clock="#f5f5f5", foot="tenpm.lab · 퇴근 후 AI 부업"),
    "threads": dict(bg="#17121f", acc="#b69cff", lab_txt="#17121f", ink="#ffffff", sub="#b3aac4", line="#2c2438", clock="#f5f5f5", foot="tenpm.lab · 쓰레드 가이드"),
    "desk":    dict(bg="#0f1d1a", acc="#5fd3a5", lab_txt="#0f1d1a", ink="#ffffff", sub="#a3bdb5", line="#21352f", clock="#f5f5f5", foot="tenpm.lab · 직장인템"),
    "affiliate": dict(bg="#1d1512", acc="#ff8a5b", lab_txt="#1d1512", ink="#ffffff", sub="#c4b0a6", line="#3a2a24", clock="#f5f5f5", foot="tenpm.lab · 제휴 프로그램 가이드"),
    "ai":      dict(bg="#0e1a24", acc="#4fd1ff", lab_txt="#0e1a24", ink="#ffffff", sub="#a3b8c6", line="#1f3140", clock="#f5f5f5", foot="tenpm.lab · AI 정보"),
    "ep":      dict(bg="#f4efe6", acc="#e2463a", lab_txt="#ffffff", ink="#1c1c1c", sub="#6b645b", line="#ddd4c6", clock="#1c1c1c", foot="tenpm.lab · AI가 시키는 대로 연재"),
}


def f(p, s):
    return ImageFont.truetype(p, s, index=1)


def guess(label):
    if "AI" in label:
        return "ai"
    if "EP" in label or "시키는 대로" in label:
        return "ep"
    if "쓰레드" in label:
        return "threads"
    if "제휴" in label:
        return "affiliate"
    if "직장인템" in label:
        return "desk"
    return "coupang"


def fit(d, text, path, size, maxw):
    while size > 30 and d.textlength(text, font=f(path, size)) > maxw:
        size -= 4
    return f(path, size)


def make(out, label, lines, sub, series=None):
    label = label.replace("AI 무료 활용", "AI 정보")  # 11/23 Ssuii: 시리즈 이름은 "AI 정보"
    c = SERIES[series or guess(label)]
    W = 1080
    im = Image.new("RGB", (W, W), c["bg"])
    d = ImageDraw.Draw(im)
    cx, cy, r = W - 150, 150, 62
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c["clock"], width=10)
    d.line((cx, cy, cx, cy - 38), fill=c["clock"], width=10)
    d.line((cx, cy, cx + 30, cy + 14), fill="#f5c400", width=10)  # 실제 로고처럼 짧은 바늘은 노랑
    lf = fit(d, label, R, 40, 720)
    d.rounded_rectangle((90, 120, 90 + d.textlength(label, font=lf) + 56, 190), radius=35, fill=c["acc"])
    d.text((118, 128), label, font=lf, fill=c["lab_txt"])
    y = 330
    for i, t in enumerate(lines):
        d.text((90, y), t, font=fit(d, t, B, 96, 900), fill=c["ink"] if i < len(lines) - 1 else c["acc"])
        y += 130
    d.text((90, y + 30), sub, font=fit(d, sub, R, 44, 900), fill=c["sub"])
    d.line((90, W - 150, W - 90, W - 150), fill=c["line"], width=3)
    d.text((90, W - 120), c["foot"], font=f(R, 38), fill=c["sub"])
    im.save(out, quality=92)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3].split("|"), sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
