import annot
U="/mnt/user-data/uploads/%s-image.png"
J=[]
def M(name, src, crop, marks=(), blurs=(), scale=1.0): J.append((name, U%src, crop, list(marks), list(blurs), scale))
# ① 키트 복사
M("k1_template_btn","4986b504",(460,122,1460,620),[dict(box=(1336,218,1438,238),label="Use this template",side="belowleft")])
M("k2_create_repo","5348ab48",(460,122,1460,620),[dict(box=(1290,250,1435,272),label="Create a new repository",side="belowleft",num="corner")])
M("k3_form","cd09fb66",(640,180,1260,750),[dict(box=(1044,278,1220,302),label="키트 이름 확인",side="below",num="corner"),
   dict(box=(672,443,784,467),label="tenpm-lab 말고 내 아이디",side="below",num="corner"),
   dict(box=(806,443,1233,467),label="사무실 이름 (영어)",side="above",num="corner"),
   dict(box=(1133,649,1220,674),label="Public",side="left"),
   dict(box=(1125,708,1234,733),label="클릭",side="left")])
M("k4_done","0e8ee5e7",(430,200,1460,620),[dict(box=(486,218,610,240),label="내 사무실 완성!",side="right",num="corner")],
   blurs=[(476,326,560,345),(1221,756,1320,780)])
# ② 사무실 문 열기
M("p1_settings","b6d9f91c",(0,130,1000,660),[dict(box=(688,170,752,192),label="Settings",side="below",num="corner"),
   dict(box=(468,615,672,637),label="Pages",side="right")])
M("p2_pages","fd526695",(460,200,1460,620),[dict(box=(710,351,855,375),label="Deploy from a branch",side="right"),
   dict(box=(710,448,772,472),label="None → main",side="below",num="corner")])
M("p3_docs","586a7e79",(460,200,1460,620),[dict(box=(710,448,880,472),label="main 과 /docs 로 고르기",side="below",num="corner"),
   dict(box=(889,448,940,472),label="Save",side="right",num="corner")])
M("p4_live","8eee4e41",(460,200,1460,620),[dict(box=(716,309,1010,323),label="내 사무실 주소",side="below",num="corner"),
   dict(box=(1169,310,1256,336),label="Visit site",side="below",num="corner")],blurs=[(788,326,850,340)])
M("p5_office","a89618b0",(340,130,1570,1040),[],scale=0.8)
# ③ 직원 꾸미기
M("c1_docs","7ce39161",(460,200,1460,620),[dict(box=(498,398,560,414),label="docs/office",side="right")],blurs=[(476,326,560,345)])
M("c2_chars","a6ae2934",(0,200,1000,450),[dict(box=(300,376,345,392),label="chars.js",side="right")],blurs=[(276,262,350,278)])
M("c3_copy","ae9347f2",(1000,200,1900,520),[dict(box=(1383,310,1405,330),label="복사 버튼",side="below",num="corner")],blurs=[(276,262,350,278)])
M("c4_claude","7e408c4f",(290,122,1920,700),[dict(box=(1731,130,1803,156),label="내용만 복사",side="below",num="corner")],scale=0.75)
M("c5_pencil","c3b9eddf",(1000,200,1900,520),[dict(box=(1432,310,1454,330),label="연필 (수정)",side="below",num="corner")])
M("c6_commit","57e9929a",(760,370,1160,790),[dict(box=(1033,743,1139,767),label="클릭",side="above",num="corner")])
M("c7_after","3fe394d3",(340,130,1570,1040),[],scale=0.8)
# 금고
M("s1_secrets_menu","9ccc02c2",(440,600,1000,960),[dict(box=(472,761,640,777),label="Secrets and variables",side="right"),
   dict(box=(482,786,560,802),label="Actions",side="right")])
M("s2_new_secret","877a31ba",(460,200,1460,800),[dict(box=(1012,601,1145,625),label="New repository secret",side="below",num="corner")])
# 예약 게시
M("a1_actions","277b5bc7",(0,130,1000,600),[dict(box=(250,170,318,192),label="Actions",side="below",num="corner"),
   dict(box=(22,307,240,326),label="예약 게시",side="right",num="corner")],blurs=[(760,494,805,508),(760,547,805,561)])
M("a2_run","bee2a843",(1000,320,1600,580),[dict(box=(1450,331,1541,356),label="Run workflow",side="left"),
   dict(box=(1437,521,1528,546),label="실행",side="left")])
# 메타
M("m1_home","4c6a1368",(260,122,1660,700),[dict(box=(1550,140,1590,164),label="로그인 (페이스북 계정)",side="belowleft",num="corner")])
M("m2_myapps","72ec2af6",(260,122,1660,500),[dict(box=(1555,140,1592,164),label="내 앱",side="belowleft",num="corner")])
M("m3_create","51935581",(340,180,1580,560),[dict(box=(1486,198,1559,230),label="앱 만들기",side="belowleft",num="corner")],blurs=[(668,402,800,416)])
M("m4_form","29907482",(540,180,1360,520),[dict(box=(564,341,1341,369),label="앱 이름 (아무거나)",side="above",num="corner"),
   dict(box=(1293,471,1341,499),label="다음",side="left")],blurs=[(566,432,900,455)])
M("m5_dash","548eece0",(0,160,900,420),[dict(box=(10,295,234,318),label="이용 사례",side="right",num="corner")])
M("m6_usecase","b812b8ee",(540,180,1600,340),[dict(box=(1483,271,1571,298),label="맞춤 설정",side="left")])
M("m7_perms","d35721bb",(420,340,1760,1000),[dict(box=(1479,387,1542,414),label="+ 추가 (팔로워 수)",side="left"),
   dict(box=(1479,816,1542,843),label="+ 추가 (댓글 읽기)",side="left")],scale=0.8)
M("m8a_settings","b5de1dc2",(160,180,1770,700),[dict(box=(184,353,405,383),label="설정",side="below",num="corner"),
   dict(box=(444,478,1746,506),label="주소 입력 후 엔터 (3칸 모두)",side="above",num="corner"),
   dict(box=(1685,656,1733,684),label="저장",side="left")],
   blurs=[(444,313,1087,343),(1104,313,1690,343),(448,481,665,505),(448,543,1000,569),(448,606,1000,632)],scale=0.8)
M("m8b_token","b5de1dc2",(430,720,1770,930),[dict(box=(1248,753,1442,780),label="테스터 추가",side="left"),
   dict(box=(1318,873,1450,901),label="토큰 생성",side="left")],blurs=[(445,825,1745,866)])
M("m9_roles","8c5af299",(720,275,1200,705),[dict(box=(733,612,1150,640),label="이걸 골라요",side="above",num="corner"),
   dict(box=(1139,663,1187,691),label="추가",side="left")])
# 쓰레드 웹사이트 권한
M("t1_settings","9b4ee27b",(0,130,1290,520),[dict(box=(160,236,320,254),label="설정",side="right"),
   dict(box=(633,392,843,427),label="설정 더 보기",side="below",num="corner"),
   dict(box=(862,230,1265,252),label="웹사이트 권한",side="below",num="corner")],scale=0.85)
M("t2_invite","0622d6ed",(620,130,1290,340),[dict(box=(1166,192,1262,222),label="초대",side="above",num="corner"),
   dict(box=(1211,239,1260,264),label="수락하면 '삭제'로 바뀜 = 정상",side="belowleft",num="left")])
for j in J:
    annot.make(j[1], j[0]+".png", j[2], j[3], j[4], j[5])
print(len(J))
