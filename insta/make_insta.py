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
    "ai": dict(bg="#0e1a24", acc="#4fd1ff", ink="#ffffff", sub="#a3b8c6", line="#1f3140", card="#142433", acc_ink="#0e1a24", warn="#ffd23f"),
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


def segs(text):
    """'**강조**' 표시를 (글자, 강조여부) 조각으로"""
    out, hi = [], False
    for k, part in enumerate(text.split("**")):
        if part:
            out.append((part, k % 2 == 1))
    return out


def rich(d, xy, text, fnt, ink, acc):
    """한 줄을 강조 조각별 색으로 그림"""
    x, y = xy
    for part, hi in segs(text):
        d.text((x, y), part, font=fnt, fill=acc if hi else ink)
        x += d.textlength(part, font=fnt)


def fit_lines(d, text, path, size, maxw, minsize=34):
    """\n 기준 줄 그대로. 가장 긴 줄이 maxw 안에 들어갈 때까지 글씨를 줄임"""
    lines = text.split("\n")
    while size > minsize and max(d.textlength(l.replace("**", ""), font=font(path, size)) for l in lines) > maxw:
        size -= 2
    return lines, font(path, size), size


def wrap_rich_old(d, text, fnt, maxw):
    """강조 표시를 유지한 채 줄바꿈 (강조 구간이 줄을 넘으면 양쪽에 ** 다시 붙임)"""
    lines = wrap(d, text.replace("**", "\u0001"), fnt, maxw) if False else None
    plain = text.replace("**", "")
    flags = []
    hi = False
    i = 0
    while i < len(text):
        if text.startswith("**", i):
            hi = not hi
            i += 2
            continue
        flags.append(hi)
        i += 1
    out, pos = [], 0
    for line in wrap(d, plain, fnt, maxw):
        # wrap 이 공백을 줄였으니 plain 에서 그 줄 위치를 찾아 강조 복원
        start = plain.find(line, pos) if line else pos
        if start < 0:
            out.append(line)
            continue
        buf, cur = "", False
        for k, ch in enumerate(line):
            f = flags[start + k]
            if f != cur:
                buf += "**"
                cur = f
            buf += ch
        if cur:
            buf += "**"
        out.append(buf)
        pos = start + len(line)
    return out


def tri(d, x, y, s, fill, ink):
    d.polygon([(x + s / 2, y), (x + s, y + s * 0.9), (x, y + s * 0.9)], fill=fill)
    d.rectangle((x + s / 2 - s * 0.05, y + s * 0.3, x + s / 2 + s * 0.05, y + s * 0.6), fill=ink)
    d.ellipse((x + s / 2 - s * 0.06, y + s * 0.68, x + s / 2 + s * 0.06, y + s * 0.8), fill=ink)


def clock(d, cx, cy, r, c):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=max(4, r // 7))
    d.line((cx, cy, cx, cy - r * 0.6), fill=c, width=max(4, r // 7))
    d.line((cx, cy, cx + r * 0.45, cy + r * 0.25), fill=c, width=max(4, r // 7))


LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")  # 실제 프로필 로고 (docs/icon.png)


def logo(im, cx, cy, size):
    lg = Image.open(LOGO).convert("RGBA").resize((size, size), Image.LANCZOS)
    im.paste(lg, (int(cx - size / 2), int(cy - size / 2)), lg)


def frame(c, i, n):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    logo(im, W - PAD - 32, PAD + 32, 64)
    d.text((PAD, H - PAD - 30), "tenpm.lab", font=font(M, 30), fill=c["sub"])
    pg = f"{i}/{n}"
    fp = font(M, 30)
    d.text((W - PAD - d.textlength(pg, font=fp), H - PAD - 30), pg, font=fp, fill=c["sub"])
    return im, d


def block(d, x, y, text, path, size, maxw, ink, acc, lh=1.32):
    """\n 으로 나눈 줄을 끊지 않고 그림 (넘치면 글씨 크기를 줄임). 다음 y 반환"""
    lines, fnt, sz = fit_lines(d, text, path, size, maxw)
    for line in lines:
        rich(d, (x, y), line, fnt, ink, acc)
        y += int(sz * lh)
    return y


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
            d.rounded_rectangle((PAD, 0, PAD + kw + 56, 76), radius=38, fill=c["acc"])
            d.text((PAD + 28, 10), cd["kicker"], font=fk, fill=c["acc_ink"])
            y = 150
            title = "\n".join(cd["title"][:-1] + ["**" + cd["title"][-1] + "**"])
            y = block(d, PAD, y, title, B, 128, maxw, c["ink"], c["acc"], 1.25)
            y = block(d, PAD, y + 30, cd.get("sub", ""), M, 48, maxw, c["sub"], c["acc"])
            hint = "넘겨서 보기  →"
            fh = font(B, 38)
            d0.text((W - PAD - d0.textlength(hint, font=fh), H - PAD - 120), hint, font=fh, fill=c["acc"])
        elif t == "point":
            y = 0
            if cd.get("num"):
                d.text((PAD, y), cd["num"], font=font(B, 150), fill=c["acc"])
                y += 210
            y = block(d, PAD, y, cd["title"], B, 92, maxw, c["ink"], c["acc"], 1.28)
            d.line((PAD, y + 30, PAD + 120, y + 30), fill=c["acc"], width=8)
            y = block(d, PAD, y + 90, cd["body"], M, 56, maxw, c["sub"], c["acc"], 1.5)
        elif t == "warn":
            tri(d, PAD, 0, 130, c["warn"], c["bg"])
            y = block(d, PAD, 180, cd["title"], B, 92, maxw, c["ink"], c["warn"], 1.28)
            y = block(d, PAD, y + 40, cd["body"], M, 56, maxw, c["sub"], c["warn"], 1.5)
        elif t == "flow":
            # 한눈에: [옛것] → [새것] 큰 알약 + 아래 날짜 타임라인
            y = block(d, PAD, 0, cd["title"], B, 92, maxw, c["ink"], c["acc"], 1.28)
            y += 70
            fo = font(B, 80)
            old, new = cd["from"], cd["to"]
            ow, nw = d.textlength(old, font=fo), d.textlength(new, font=fo)
            pw_o, pw_n = ow + 110, nw + 110
            gap = 180
            x0 = (W - (pw_o + gap + pw_n)) / 2
            d.rounded_rectangle((x0, y, x0 + pw_o, y + 150), radius=75, fill=c["card"])
            d.text((x0 + 55, y + 22), old, font=fo, fill=c["sub"])
            ax = x0 + pw_o + 35
            d.line((ax, y + 75, ax + gap - 80, y + 75), fill=c["acc"], width=10)
            d.polygon([(ax + gap - 70, y + 75), (ax + gap - 100, y + 50), (ax + gap - 100, y + 100)], fill=c["acc"])
            x1 = x0 + pw_o + gap
            d.rounded_rectangle((x1, y, x1 + pw_n, y + 150), radius=75, fill=c["acc"])
            d.text((x1 + 55, y + 22), new, font=fo, fill=c["acc_ink"])
            y += 260
            # 타임라인 (세로)
            steps = cd["steps"]
            lx = PAD + 30
            d.line((lx, y + 30, lx, y + 30 + 170 * (len(steps) - 1)), fill=c["line"], width=8)
            for k, st in enumerate(steps):
                cy = y + 30 + 170 * k
                hot = st.get("hot")
                col = c["warn"] if hot else c["acc"]
                d.ellipse((lx - 26, cy - 26, lx + 26, cy + 26), fill=col)
                d.text((lx + 70, cy - 52), st["date"], font=font(B, 52), fill=col)
                d.text((lx + 70, cy + 12), st["text"], font=font(M, 46), fill=c["ink"])
        elif t == "check":
            y = block(d, PAD, 0, cd["title"], B, 92, maxw, c["ink"], c["acc"], 1.28)
            y += 50
            for item in cd["items"]:
                d.rounded_rectangle((PAD, y, W - PAD, y + 150), radius=28, fill=c["card"])
                d.rounded_rectangle((PAD + 36, y + 47, PAD + 92, y + 103), radius=12, outline=c["acc"], width=6)
                d.line((PAD + 48, y + 75, PAD + 60, y + 89), fill=c["acc"], width=7)
                d.line((PAD + 60, y + 89, PAD + 82, y + 58), fill=c["acc"], width=7)
                lines, fnt, sz = fit_lines(d, item, B, 50, maxw - 170)
                rich(d, (PAD + 130, y + 75 - sz * 0.62), lines[0], fnt, c["ink"], c["acc"])
                y += 180
        elif t == "end":
            logo(layer, W // 2, 90, 180)
            y = 270
            fe = font(B, 72)
            for line in cd["title"].split("\n"):
                d.text(((W - d.textlength(line, font=fe)) / 2, y), line, font=fe, fill=c["ink"])
                y += 96
            fs = font(M, 46)
            for line in cd.get("sub", "").split("\n"):
                d.text(((W - d.textlength(line, font=fs)) / 2, y + 20), line, font=fs, fill=c["sub"])
                y += 64
            h = cd.get("handle", "")
            fh = font(B, 52)
            hw = d.textlength(h, font=fh)
            d.rounded_rectangle(((W - hw) / 2 - 40, y + 70, (W + hw) / 2 + 40, y + 160), radius=45, fill=c["acc"])
            d.text(((W - hw) / 2, y + 82), h, font=fh, fill=c["acc_ink"])
            if cd.get("note"):
                fn = font(M, 30)
                d0.text(((W - d0.textlength(cd["note"], font=fn)) / 2, H - PAD - 110), cd["note"], font=fn, fill=c["sub"])
        # 내용이 있는 범위만 잘라 화면 가운데에 붙이기
        from PIL import ImageChops
        box = ImageChops.difference(layer, Image.new("RGB", layer.size, c["bg"])).getbbox()
        if box:
            part = layer.crop((0, box[1], W, box[3]))
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
