# 정보 글용 본문 그림 (따뜻한 크림 톤). 연말정산 미리보기 글 4장
from PIL import Image, ImageDraw, ImageFont
B="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; R="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
f=lambda p,s: ImageFont.truetype(p,s,index=1)
BG,INK,SUB,ACC,SOFT,LINE="#fbf4ea","#3b2f2a","#8c7b70","#d9764f","#f6dfc8","#e9dccd"
def base(kicker,title):
    im=Image.new("RGB",(1080,1080),BG); d=ImageDraw.Draw(im)
    d.text((80,80),kicker,font=f(R,38),fill=SUB); d.text((80,135),title,font=f(B,64),fill=INK)
    d.text((80,1000),"tenpm.lab · 출처 국세청 홈택스",font=f(R,28),fill="#a8968a")
    return im,d

# 1. 경로
im,d=base("10분이면 끝","미리보기 들어가는 길")
steps=[("홈택스 로그인","간편인증(카카오·네이버 등) 가능"),("편리한 연말정산","메인 화면 메뉴"),("연말정산 미리보기","1~9월 카드 사용액 자동 반영"),("10~12월 예상액 입력","→ 예상 환급액 확인")]
y=280
for i,(t,s) in enumerate(steps):
    d.rounded_rectangle((80,y,1000,y+140),radius=28,fill="#ffffff",outline=LINE,width=3)
    d.ellipse((110,y+35,180,y+105),fill=ACC); d.text((145,y+70),str(i+1),font=f(B,40),fill="#fff",anchor="mm")
    d.text((210,y+22),t,font=f(B,46),fill=INK); d.text((210,y+85),s,font=f(R,30),fill=SUB)
    if i<3: d.polygon([(530,y+150),(570,y+150),(550,y+172)],fill=ACC)
    y+=180
im.save("blog/thumbs/i_yearend_path.jpg",quality=92)

# 2. 25% 문턱
im,d=base("연봉 5천만 원이라면","공제는 '문턱' 넘은 부분부터")
d.text((80,280),"1년 카드 사용액 2,000만 원 예시",font=f(R,36),fill=SUB)
x0,x1=80,1000; th=x0+int((x1-x0)*1250/2000)
d.rounded_rectangle((x0,350,x1,470),radius=24,fill=SOFT)
d.rounded_rectangle((th,350,x1,470),radius=24,fill=ACC); d.rectangle((th,350,th+30,470),fill=ACC)
d.text(((x0+th)//2,410),"1,250만 원",font=f(B,44),fill=INK,anchor="mm")
d.text(((th+x1)//2,410),"750만 원",font=f(B,44),fill="#fff",anchor="mm")
d.line((th,330,th,500),fill=INK,width=5)
d.text((x0,500),"총급여의 25% = 공제 0원",font=f(R,34),fill=SUB)
d.text((th-20,540),"여기부터 공제 ▶",font=f(B,36),fill=ACC)
d.rounded_rectangle((80,650,1000,920),radius=28,fill="#ffffff",outline=LINE,width=3)
d.text((120,690),"문턱 안쪽은 어떤 카드를 써도 공제 0",font=f(B,40),fill=INK)
d.text((120,760),"그래서 미리보기로 '이미 넘었는지'를",font=f(R,36),fill=SUB)
d.text((120,815),"먼저 확인하는 게 핵심",font=f(R,36),fill=SUB)
im.save("blog/thumbs/i_yearend_threshold.jpg",quality=92)

# 3. 결정 흐름
im,d=base("미리보기 결과를 보고","남은 달 뭐로 결제할까?")
d.rounded_rectangle((240,290,840,400),radius=30,fill=INK)
d.text((540,345),"카드 25% 이미 넘었음?",font=f(B,44),fill="#fff",anchor="mm")
for cx,lab,title,lines,col in [(300,"넘었음","체크카드·현금영수증",["공제율 30%","신용카드의 2배"],ACC),(780,"아직","신용카드로 채우기",["문턱 안쪽은 공제 0","할인·적립 챙기기"],"#b9a48f")]:
    d.line((540,400,cx,520),fill=col,width=6)
    d.text((cx,470),lab,font=f(B,36),fill=col,anchor="mm")
    d.rounded_rectangle((cx-230,530,cx+230,860),radius=30,fill="#ffffff",outline=col,width=5)
    d.text((cx,600),title,font=f(B,40),fill=INK,anchor="mm")
    for i,l in enumerate(lines): d.text((cx,690+i*70),l,font=f(R,36),fill=SUB,anchor="mm")
d.text((80,910),"전통시장·대중교통은 결제수단 상관없이 40%",font=f(R,32),fill=SUB)
im.save("blog/thumbs/i_yearend_flow.jpg",quality=92)

# 4. 한도 + 자녀 + 정리
im,d=base("같이 확인할 것","한도 · 자녀세액공제")
d.rounded_rectangle((80,270,1000,520),radius=28,fill="#ffffff",outline=LINE,width=3)
d.text((120,300),"카드 공제 기본 한도",font=f(B,42),fill=INK)
d.text((120,375),"총급여 7천만 원 이하  →  300만 원",font=f(R,36),fill=SUB)
d.text((120,435),"7천만 원 초과  →  250만 원 (자녀 있으면 ↑)",font=f(R,36),fill=SUB)
d.rounded_rectangle((80,560,1000,900),radius=28,fill="#ffffff",outline=LINE,width=3)
d.text((120,590),"자녀세액공제 (8세 이상 자녀)",font=f(B,42),fill=INK)
for i,(a,b) in enumerate([("첫째","25만 원"),("둘째","30만 원"),("셋째부터","1명당 40만 원")]):
    d.text((120,670+i*70),a,font=f(R,38),fill=SUB); d.text((960,670+i*70),b,font=f(B,38),fill=ACC,anchor="ra")
im.save("blog/thumbs/i_yearend_limit.jpg",quality=92)
