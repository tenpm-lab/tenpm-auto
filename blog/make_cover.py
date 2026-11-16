from PIL import Image, ImageDraw, ImageFont
B="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; R="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
f=lambda p,s: ImageFont.truetype(p,s,index=1)
W=H=1440; im=Image.new("RGB",(W,H),"#12141b"); d=ImageDraw.Draw(im)
# faint big clock
cx,cy,r=W//2,560,330
d.ellipse((cx-r,cy-r,cx+r,cy+r),outline="#1f2330",width=34)
d.line((cx,cy,cx,cy-220),fill="#1f2330",width=34); d.line((cx,cy,cx+170,cy+80),fill="#5a4a10",width=34)
d.ellipse((cx-26,cy-26,cx+26,cy+26),fill="#1f2330")
# small dots (night)
import random; random.seed(10)
for _ in range(60):
    x,y=random.randint(0,W),random.randint(0,H); s=random.choice([2,2,3,4])
    d.ellipse((x,y,x+s,y+s),fill="#3a3f4f")
t1="퇴근 후 밤 10시,"; t2="AI가 시키는 대로"
for t,y,c in [(t1,470,"#ffffff"),(t2,580,"#f5c400")]:
    w=d.textlength(t,font=f(B,96)); d.text(((W-w)/2,y),t,font=f(B,96),fill=c)
s="0원부터 공개하는 부업 실험 기록"; w=d.textlength(s,font=f(R,46)); d.text(((W-w)/2,730),s,font=f(R,46),fill="#aab0bd")
im.save("blog/thumbs/cover_mobile.jpg",quality=92)
