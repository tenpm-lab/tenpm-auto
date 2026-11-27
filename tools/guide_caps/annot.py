# 캡처 정리: 브라우저 위쪽 잘라내기 + 빨간 네모 + 번호 + 설명 말풍선 + 가리기 + 워터마크
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
FONT_DIR = "/home/claude/fonts"
NOTO = "/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"
LOGO = "/home/claude/tenpm-auto/insta/logo.png"
RED = (239, 68, 68)
def font(sz, w="Bold"):
    p = os.path.join(FONT_DIR, f"Pretendard-{'ExtraBold' if w=='Black' else w}.otf")
    if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.truetype(NOTO % w, sz, index=1)

def watermark(im, opacity=0.45):
    """오른쪽 아래 작은 워터마크. opacity로 전체를 옅게 (내용 가독성 방해 X)"""
    t = "@tenpm.lab"; tf = font(max(15, im.width // 60), "Bold")
    tmp = ImageDraw.Draw(im); w = tmp.textlength(t, font=tf); h = tf.size
    lg = Image.open(LOGO).convert("RGBA"); s = int(h * 1.4); lg = lg.resize((s, s), Image.LANCZOS)
    pad = 9; bw, bh = int(s + 7 + w + pad * 2), int(s + pad)
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2, fill=(40, 40, 48, 150))
    layer.paste(lg, (pad, int(pad / 2)), lg)
    d.text((pad + s + 7, bh / 2), t, font=tf, fill=(255, 255, 255, 255), anchor="lm")
    a = layer.split()[3].point(lambda v: int(v * opacity)); layer.putalpha(a)
    base = im.convert("RGBA"); base.alpha_composite(layer, (im.width - bw - 12, im.height - bh - 8))
    im.paste(base.convert("RGB"))

def make(src, out, crop, marks, blurs=(), scale=1.0):
    im = Image.open(src).convert("RGB")
    for (x1, y1, x2, y2) in blurs:
        im.paste(im.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(12)), (x1, y1))
    im = im.crop(crop); ox, oy = crop[0], crop[1]
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    S = scale
    base = im.convert("RGBA"); over = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
    for i, m in enumerate(marks, 1):
        x1, y1, x2, y2 = ((m["box"][0] - ox) * S, (m["box"][1] - oy) * S, (m["box"][2] - ox) * S, (m["box"][3] - oy) * S)
        d.rounded_rectangle((x1 - 6, y1 - 6, x2 + 6, y2 + 6), radius=10, outline=RED + (255,), width=4)
        n = m.get("n", str(i)); r = 16
        cx, cy = (x1 - 30, (y1 + y2) / 2) if m.get("num", "left") == "left" else (x1 - 6, y1 - 6)
        d.ellipse((cx - r + 2, cy - r + 3, cx + r + 2, cy + r + 3), fill=(0, 0, 0, 60))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED + (255,), outline=(255, 255, 255, 255), width=3)
        d.text((cx, cy - 1), n, font=font(19, "Bold"), fill="white", anchor="mm")
        if m.get("label"):
            t = m["label"]; tf = font(20, "SemiBold" if os.path.exists(os.path.join(FONT_DIR, "Pretendard-SemiBold.otf")) else "Medium")
            w = d.textlength(t, font=tf); bw, bh = w + 28, 38
            side = m.get("side", "right")
            if side == "right": tx, ty = x2 + 22, (y1 + y2) / 2 - bh / 2
            elif side == "left": tx, ty = x1 - 52 - bw, (y1 + y2) / 2 - bh / 2
            elif side == "below": tx, ty = x1, y2 + 16
            elif side == "belowleft": tx, ty = x2 - bw, y2 + 16
            else: tx, ty = x1, y1 - bh - 16
            d.rounded_rectangle((tx + 2, ty + 3, tx + bw + 2, ty + bh + 3), radius=bh // 2, fill=(0, 0, 0, 50))
            d.rounded_rectangle((tx, ty, tx + bw, ty + bh), radius=bh // 2, fill=RED + (255,))
            d.text((tx + bw / 2, ty + bh / 2 - 1), t, font=tf, fill="white", anchor="mm")
    im = Image.alpha_composite(base, over).convert("RGB")
    # 워터마크는 아래쪽 여백 띠에 (버튼을 가리지 않게)
    bg = im.getpixel((im.width - 3, im.height - 3))
    canvas = Image.new("RGB", (im.width, im.height + 44), bg); canvas.paste(im, (0, 0)); im = canvas
    watermark(im)
    im.save(out, quality=92)
