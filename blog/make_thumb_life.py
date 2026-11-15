# 일상·육아·정보성 글용 썸네일 (밝고 따뜻한 감성). 사용법: python3 make_thumb_life.py out.jpg "라벨" "줄1|줄2" "부제"
import sys
from PIL import Image, ImageDraw, ImageFont
B="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; R="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def f(p,s): return ImageFont.truetype(p,s,index=1)
def make(out,label,lines,sub):
    W=1080; im=Image.new("RGB",(W,W),"#fbf4ea"); d=ImageDraw.Draw(im)
    # soft blobs
    d.ellipse((W-330,-120,W+120,330),fill="#f6dfc8"); d.ellipse((-160,W-300,260,W+120),fill="#e6efe1")
    d.ellipse((W-210,120,W-150,180),fill="#f2a98a")
    d.rounded_rectangle((90,130,90+d.textlength(label,font=f(R,40))+56,200),radius=35,fill="#f2a98a")
    d.text((118,138),label,font=f(R,40),fill="#ffffff")
    y=330
    for i,t in enumerate(lines):
        d.text((90,y),t,font=f(B,92),fill="#3b2f2a" if i<len(lines)-1 else "#d9764f"); y+=125
    d.text((90,y+30),sub,font=f(R,42),fill="#8c7b70")
    d.text((90,W-130),"tenpm.lab · 일상 기록",font=f(R,36),fill="#a8968a")
    im.save(out,quality=92)
make(sys.argv[1], sys.argv[2], sys.argv[3].split("|"), sys.argv[4])
