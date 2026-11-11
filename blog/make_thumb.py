import sys
from PIL import Image, ImageDraw, ImageFont
B="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; R="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def f(p,s): return ImageFont.truetype(p,s,index=1)
def make(out,label,lines,sub):
    W=1080; im=Image.new("RGB",(W,W),"#12141b"); d=ImageDraw.Draw(im)
    # clock mark
    cx,cy,r=W-150,150,62
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline="#f5f5f5",width=10)
    d.line((cx,cy,cx,cy-38),fill="#f5f5f5",width=10); d.line((cx,cy,cx+30,cy+14),fill="#f5c400",width=10)
    d.rounded_rectangle((90,120,90+d.textlength(label,font=f(R,40))+56,190),radius=35,fill="#f5c400")
    d.text((118,128),label,font=f(R,40),fill="#12141b")
    y=330
    for i,t in enumerate(lines):
        d.text((90,y),t,font=f(B,96),fill="#ffffff" if i<len(lines)-1 else "#f5c400"); y+=130
    d.text((90,y+30),sub,font=f(R,44),fill="#aab0bd")
    d.line((90,W-150,W-90,W-150),fill="#2a2e3a",width=3)
    d.text((90,W-120),"tenpm.lab · 퇴근 후 AI 부업",font=f(R,38),fill="#8a90a0")
    im.save(out,quality=92)
make(*sys.argv[1:2], sys.argv[2], sys.argv[3].split("|"), sys.argv[4])
