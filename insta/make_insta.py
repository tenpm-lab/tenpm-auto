"""인스타 카드뉴스 (1080x1350, 4:5). 그림만 넘겨봐도 이해되게: 한 장에 메시지 하나.
사용: python insta/make_insta.py spec.json 출력폴더
spec = {"series":"ai", "cards":[
  {"type":"cover","kicker":"AI 정보","title":["윗줄","강조줄"],"sub":"부제"},
  {"type":"point","num":"01","title":"제목","body":"설명 1~2줄 (\\n 줄바꿈)"},
  {"type":"check","title":"제목","items":["할 것1","할 것2"]},
  {"type":"end","title":"마무리 한 줄","sub":"설명","handle":"@tenpm.lab","note":"출처"}]}"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
W, H, PAD = 1080, 1350, 96
PAL = {
    "ai": dict(bg="#0e1a24", acc="#4fd1ff", ink="#ffffff", sub="#a3b8c6", line="#1f3140", card="#142433", acc_ink="#0e1a24"),
}


def font(p, s):
    return ImageFont.truetype(p, s, index=1)


def wrap(d, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            t = (line + " " + word).strip()
            if d.textlength(t, font=fnt) <= maxw:
                line = t
            else:
                if line:
                    out.append(line)
                line = word
        out.append(line)
    return out


def clock(d, cx, cy, r, c):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=max(4, r // 7))
    d.line((cx, cy, cx, cy - r * 0.6), fill=c, width=max(4, r // 7))
    d.line((cx, cy, cx + r * 0.45, cy + r * 0.25), fill=c, width=max(4, r // 7))


def frame(c, i, n):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    clock(d, W - PAD - 26, PAD + 26, 26, c["sub"])
    d.text((PAD, H - PAD - 30), "tenpm.lab", font=font(M, 30), fill=c["sub"])
    pg = f"{i}/{n}"
    fp = font(M, 30)
    d.text((W - PAD - d.textlength(pg, font=fp), H - PAD - 30), pg, font=fp, fill=c["sub"])
    return im, d


def make(spec, outdir):
    c = PAL[spec.get("series", "ai")]
    cards = spec["cards"]
    n = len(cards)
    os.makedirs(outdir, exist_ok=True)
    files = []
    for i, cd in enumerate(cards, 1):
        im, d0 = frame(c, i, n)
        layer = Image.new("RGB", (W, H * 2), c["bg"])
        d = ImageDraw.Draw(layer)
        maxw = W - PAD * 2
        t = cd["type"]
        if t == "cover":
            fk = font(B, 40)
            kw = d.textlength(cd["kicker"], font=fk)
            d.rounded_rectangle((PAD, 300, PAD + kw + 56, 376), radius=38, fill=c["acc"])
            d.text((PAD + 28, 310), cd["kicker"], font=fk, fill=c["acc_ink"])
            y = 450
            for k, line in enumerate(cd["title"]):
                fs = 124
                while d.textlength(line, font=font(B, fs)) > maxw:
                    fs -= 6
                d.text((PAD, y), line, font=font(B, fs), fill=c["acc"] if k == len(cd["title"]) - 1 else c["ink"])
                y += int(fs * 1.28)
            for line in wrap(d, cd.get("sub", ""), font(M, 46), maxw):
                d.text((PAD, y + 30), line, font=font(M, 46), fill=c["sub"])
                y += 62
            hint = "넘겨서 보기  →"
            fh = font(B, 38)
            d0.text((W - PAD - d0.textlength(hint, font=fh), H - PAD - 120), hint, font=fh, fill=c["acc"])
        elif t == "point":
            y = 250
            if cd.get("num"):
                d.text((PAD, y), cd["num"], font=font(B, 150), fill=c["acc"])
                y += 210
            for line in wrap(d, cd["title"], font(B, 92), maxw):
                d.text((PAD, y), line, font=font(B, 92), fill=c["ink"])
                y += 118
            d.line((PAD, y + 30, PAD + 120, y + 30), fill=c["acc"], width=8)
            y += 90
            for line in wrap(d, cd["body"], font(M, 56), maxw):
                d.text((PAD, y), line, font=font(M, 56), fill=c["sub"] if line else c["sub"])
                y += 84
        elif t == "check":
            y = 250
            for line in wrap(d, cd["title"], font(B, 92), maxw):
                d.text((PAD, y), line, font=font(B, 92), fill=c["ink"])
                y += 118
            y += 50
            for item in cd["items"]:
                d.rounded_rectangle((PAD, y, W - PAD, y + 150), radius=28, fill=c["card"])
                d.rounded_rectangle((PAD + 36, y + 47, PAD + 92, y + 103), radius=12, outline=c["acc"], width=6)
                d.line((PAD + 48, y + 75, PAD + 60, y + 89), fill=c["acc"], width=7)
                d.line((PAD + 60, y + 89, PAD + 82, y + 58), fill=c["acc"], width=7)
                lines = wrap(d, item, font(B, 50), maxw - 170)
                yy = y + 75 - len(lines) * 30
                for line in lines:
                    d.text((PAD + 130, yy), line, font=font(B, 50), fill=c["ink"])
                    yy += 58
                y += 180
        elif t == "end":
            clock(d, W // 2, 420, 90, c["ink"])
            y = 600
            for line in wrap(d, cd["title"], font(B, 72), maxw):
                d.text(((W - d.textlength(line, font=font(B, 72))) / 2, y), line, font=font(B, 72), fill=c["ink"])
                y += 96
            for line in wrap(d, cd.get("sub", ""), font(M, 46), maxw):
                d.text(((W - d.textlength(line, font=font(M, 46))) / 2, y + 20), line, font=font(M, 46), fill=c["sub"])
                y += 64
            h = cd.get("handle", "")
            fh = font(B, 52)
            hw = d.textlength(h, font=fh)
            d.rounded_rectangle(((W - hw) / 2 - 40, y + 70, (W + hw) / 2 + 40, y + 160), radius=45, fill=c["acc"])
            d.text(((W - hw) / 2, y + 82), h, font=fh, fill=c["acc_ink"])
            if cd.get("note"):
                fn = font(M, 30)
                d0.text(((W - d0.textlength(cd["note"], font=fn)) / 2, H - PAD - 110), cd["note"], font=fn, fill=c["sub"])
        # 내용이 있는 범위만 잘라 화면 가운데(위아래 여백 사이)에 붙이기
        bg = Image.new("RGB", layer.size, c["bg"])
        from PIL import ImageChops
        box = ImageChops.difference(layer, bg).getbbox()
        if box:
            top, bot = box[1], box[3]
            part = layer.crop((0, top, W, bot))
            area_top, area_bot = 190, H - 190
            y0 = area_top + max(0, (area_bot - area_top - part.height) // 2)
            if t == "cover":
                y0 = max(area_top, y0 - 60)
            im.paste(part, (0, y0))
        p = os.path.join(outdir, f"{i:02d}.jpg")
        im.save(p, quality=92)
        files.append(p)
    return files


if __name__ == "__main__":
    print("\n".join(make(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])))
