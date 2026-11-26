// 텐피엠 AI 사무실 직원 캐릭터 (동물 친구들 + 표정 8가지)
// drawChar(id, expr) → SVG 문자열. expr: normal, focus, busy, happy, sleepy, surprise, sad, excited
(function(){
const HEAD={
 panda:{fur:"#fff",ears:`<circle cx="-22" cy="-74" r="9" fill="#2b2b2b"/><circle cx="22" cy="-74" r="9" fill="#2b2b2b"/>`,face:`<ellipse cx="-11" cy="-47" rx="8.5" ry="9.5" fill="#2b2b2b" transform="rotate(-20 -11 -47)"/><ellipse cx="11" cy="-47" rx="8.5" ry="9.5" fill="#2b2b2b" transform="rotate(20 11 -47)"/>`,dark:1},
 fox:{fur:"#ff9a4d",ears:`<path d="M-28,-60 L-26,-90 L-8,-72Z" fill="#ff9a4d"/><path d="M28,-60 L26,-90 L8,-72Z" fill="#ff9a4d"/><path d="M-24,-66 L-23,-82 L-13,-72Z" fill="#2b2118"/><path d="M24,-66 L23,-82 L13,-72Z" fill="#2b2118"/>`,face:`<path d="M-30,-48 Q-16,-44 0,-30 Q16,-44 30,-48 Q30,-24 0,-23 Q-30,-24 -30,-48Z" fill="#fff4e8"/>`},
 cat:{fur:"#ffd7a8",ears:`<path d="M-26,-62 L-24,-88 L-8,-72Z" fill="#ffd7a8"/><path d="M26,-62 L24,-88 L8,-72Z" fill="#ffd7a8"/><path d="M-22,-68 L-21,-80 L-13,-72Z" fill="#ffb3c1"/><path d="M22,-68 L21,-80 L13,-72Z" fill="#ffb3c1"/>`,face:`<path d="M-6,-74 q3,6 0,10 M0,-76 v12 M6,-74 q-3,6 0,10" stroke="#e8b07c" stroke-width="2" fill="none"/>`},
 bear:{fur:"#c8915f",ears:`<circle cx="-22" cy="-74" r="10" fill="#c8915f"/><circle cx="22" cy="-74" r="10" fill="#c8915f"/><circle cx="-22" cy="-74" r="5" fill="#a8744a"/><circle cx="22" cy="-74" r="5" fill="#a8744a"/>`,face:`<ellipse cx="0" cy="-38" rx="11" ry="8" fill="#fff3e6"/>`},
 rabbit:{fur:"#fff3f0",ears:`<ellipse cx="-11" cy="-90" rx="7" ry="20" fill="#fff3f0"/><ellipse cx="11" cy="-90" rx="7" ry="20" fill="#fff3f0"/><ellipse cx="-11" cy="-88" rx="3.5" ry="14" fill="#ffb3c1"/><ellipse cx="11" cy="-88" rx="3.5" ry="14" fill="#ffb3c1"/>`,face:""},
 squirrel:{fur:"#d9884a",ears:`<path d="M-24,-64 Q-30,-88 -14,-78Z" fill="#d9884a"/><path d="M24,-64 Q30,-88 14,-78Z" fill="#d9884a"/>`,face:`<ellipse cx="0" cy="-38" rx="13" ry="9" fill="#fff0de"/>`,tail:`<path d="M18,-8 Q50,-10 44,-46 Q40,-66 26,-58 Q40,-40 18,-20Z" fill="#c9743a"/>`},
 hamster:{fur:"#ffcf8a",ears:`<circle cx="-20" cy="-74" r="7" fill="#f2a95a"/><circle cx="20" cy="-74" r="7" fill="#f2a95a"/>`,face:`<ellipse cx="-17" cy="-38" rx="9" ry="8" fill="#fff0de"/><ellipse cx="17" cy="-38" rx="9" ry="8" fill="#fff0de"/>`},
 dog:{fur:"#f2d2a2",ears:`<ellipse cx="-28" cy="-56" rx="9" ry="16" fill="#b9864f" transform="rotate(20 -28 -56)"/><ellipse cx="28" cy="-56" rx="9" ry="16" fill="#b9864f" transform="rotate(-20 28 -56)"/>`,face:`<ellipse cx="0" cy="-38" rx="11" ry="8" fill="#fff3e6"/><ellipse cx="12" cy="-56" rx="7" ry="8" fill="#d9a970"/>`},
 owl:{fur:"#8d6e9e",ears:`<path d="M-26,-66 L-30,-84 L-14,-74Z" fill="#8d6e9e"/><path d="M26,-66 L30,-84 L14,-74Z" fill="#8d6e9e"/>`,face:`<circle cx="-11" cy="-48" r="10" fill="#f6ecd9"/><circle cx="11" cy="-48" r="10" fill="#f6ecd9"/><path d="M-3,-40 L3,-40 L0,-34Z" fill="#f5b940"/>`,beak:1},
 turtle:{fur:"#9bd18a",ears:"",face:"",shell:`<ellipse cx="0" cy="-16" rx="26" ry="18" fill="#6b8f4e"/><path d="M-14,-24 h28 M-18,-12 h36 M0,-32 v32" stroke="#557539" stroke-width="2"/>`},
 penguin:{fur:"#2f3446",ears:"",face:`<path d="M-24,-50 Q-22,-30 0,-27 Q22,-30 24,-50 Q16,-66 0,-58 Q-16,-66 -24,-50Z" fill="#fff"/><path d="M-4,-40 L4,-40 L0,-34Z" fill="#f59e0b"/>`,beak:1,feet:"#f59e0b"},
 raccoon:{fur:"#a7a9b4",ears:`<path d="M-26,-64 L-24,-86 L-10,-74Z" fill="#a7a9b4"/><path d="M26,-64 L24,-86 L10,-74Z" fill="#a7a9b4"/>`,face:`<path d="M-26,-52 Q-11,-40 0,-50 Q11,-40 26,-52 Q20,-40 0,-42 Q-20,-40 -26,-52Z" fill="#3a3d4a"/><ellipse cx="0" cy="-38" rx="10" ry="7" fill="#f2f2f5"/>`,dark:1},
 duck:{fur:"#fff36b",ears:`<path d="M-2,-76 q4,-12 10,-6" stroke="#f5d000" stroke-width="3" fill="none"/>`,face:`<ellipse cx="0" cy="-38" rx="12" ry="6" fill="#f59e0b"/>`,beak:1,feet:"#f59e0b"},
};
const ACC={
 glasses:`<circle cx="-11" cy="-48" r="8" fill="none" stroke="#2b2e3d" stroke-width="2.2"/><circle cx="11" cy="-48" r="8" fill="none" stroke="#2b2e3d" stroke-width="2.2"/><path d="M-3,-48 h6" stroke="#2b2e3d" stroke-width="2"/>`,
 headset:`<path d="M-30,-52 Q-30,-86 0,-86 Q30,-86 30,-52" stroke="#2b2e3d" stroke-width="4" fill="none"/><rect x="-36" y="-58" width="9" height="16" rx="4" fill="#2b2e3d"/><rect x="27" y="-58" width="9" height="16" rx="4" fill="#2b2e3d"/><path d="M-32,-44 q4,10 16,9" stroke="#2b2e3d" stroke-width="2" fill="none"/>`,
 mug:`<rect x="20" y="-22" width="12" height="13" rx="3" fill="#fff"/><path d="M32,-19 q5,3 0,7" stroke="#fff" stroke-width="2" fill="none"/>`,
 pen:`<rect x="24" y="-74" width="4" height="18" rx="2" fill="#f87171" transform="rotate(35 26 -65)"/>`,
 watch:`<circle cx="-22" cy="-12" r="4.5" fill="#f4f1ea" stroke="#2b2e3d" stroke-width="1.5"/><path d="M-22,-12 v-3 M-22,-12 h2" stroke="#2b2e3d" stroke-width="1"/>`,
 apron:`<path d="M-12,-26 h24 v22 q-12,4 -24,0Z" fill="#fef3c7"/><text x="0" y="-11" font-size="7" font-weight="900" text-anchor="middle" fill="#b45309">점장</text>`,
 bell:`<text x="16" y="-70" font-size="14">🔔</text>`,
 earphone:`<circle cx="-27" cy="-46" r="3.5" fill="#fff"/><circle cx="27" cy="-46" r="3.5" fill="#fff"/><path d="M-27,-43 q2,14 10,18 M27,-43 q-2,14 -10,18" stroke="#fff" stroke-width="1.2" fill="none"/>`,
 calc:`<rect x="17" y="-26" width="14" height="18" rx="2" fill="#2b2e3d"/><rect x="19" y="-24" width="10" height="4" fill="#9be7c4"/><circle cx="21" cy="-15" r="1.2" fill="#fff"/><circle cx="25" cy="-15" r="1.2" fill="#fff"/><circle cx="21" cy="-11" r="1.2" fill="#fff"/><circle cx="25" cy="-11" r="1.2" fill="#fff"/>`,
 magnifier:`<circle cx="30" cy="-26" r="8" fill="#bfe8ff" fill-opacity=".5" stroke="#2b2e3d" stroke-width="2.5"/><path d="M24,-20 l-8,8" stroke="#2b2e3d" stroke-width="3" stroke-linecap="round"/>`,
 hat:`<path d="M-24,-70 Q0,-96 24,-70Z" fill="#5b4636"/><ellipse cx="0" cy="-70" rx="30" ry="5" fill="#5b4636"/>`,
 report:`<rect x="16" y="-28" width="16" height="20" rx="2" fill="#fff"/><path d="M19,-23 h10 M19,-19 h10 M19,-15 h7" stroke="#9aa1b5" stroke-width="1.2"/>`,
 key:`<text x="18" y="-10" font-size="14">🔑</text>`,
 bowtie:`<path d="M-7,-28 L0,-25 L-7,-21Z M7,-28 L0,-25 L7,-21Z" fill="#e05252"/>`,
 camera:`<rect x="14" y="-26" width="20" height="14" rx="3" fill="#2b2e3d"/><circle cx="24" cy="-19" r="4.5" fill="#60a5fa" stroke="#fff" stroke-width="1"/>`,
 badge:`<rect x="-9" y="-22" width="18" height="9" rx="2" fill="#fff"/><text x="0" y="-15.5" font-size="6" font-weight="900" text-anchor="middle" fill="#12131a">인턴</text>`,
};
const TEAM={
 editor:{rank:"부장",a:"panda",shirt:"#f5b940",ai:1,acc:["headset","glasses","mug"],animal:"판다",say:["자, 이번 주 숫자 봅시다","일요일엔 내가 출근하지","책 원고는 내가 맡지"]},
 planner:{rank:"차장",a:"fox",shirt:"#fde68a",ai:1,acc:["headset","pen"],animal:"여우",say:["아이디어 떠올랐어요!","내일 글은 제가 써둘게요","퇴근 전에 기획안 하나!"]},
 deal:{rank:"과장",a:"bear",shirt:"#f97316",tie:"none",acc:["apron"],animal:"곰",say:["이거 싸다, 진짜 싸다","장바구니 꽉 찼어요","오늘도 3개 올립니다"]},
 weekly:{rank:"과장",a:"owl",shirt:"#38bdf8",acc:["glasses","report"],animal:"부엉이",say:["주간 보고 올립니다","숫자는 거짓말 안 해요","일요일 저녁이 제 시간"]},
 poster:{rank:"대리",a:"cat",shirt:"#60a5fa",acc:["watch"],animal:"고양이",say:["정시 게시 완료!","1분도 안 늦어요","다음 글 대기 중!"]},
 check:{rank:"대리",a:"dog",shirt:"#f87171",acc:["hat","magnifier"],animal:"강아지",say:["범인은 채널 아이디!","수상한 냄새가…","오늘 숫자 이상 무!"]},
 reply:{rank:"사원",a:"rabbit",shirt:"#a78bfa",acc:["bell"],animal:"토끼",say:["댓글 왔나요?!","알림 소리 들렸어요!","링크 바로 드릴게요"]},
 stats:{rank:"사원",a:"hamster",shirt:"#34d399",acc:["calc"],animal:"햄스터",say:["팔로워 +1 기록 완료","볼에 숫자 저장 중","조회수 세는 중~"]},
 gold:{rank:"MZ 사원",a:"squirrel",shirt:"#facc15",tie:"none",acc:["earphone"],animal:"다람쥐",say:["특가 떴다 ㄱㄱ","아침이 제일 바빠요","퇴근은 칼퇴요 ㅎ"]},
 key:{rank:"고문",a:"turtle",shirt:"#94a3b8",tie:"wide",acc:["key","glasses"],animal:"거북이",say:["보름에 한 번 출근합니다","열쇠는 내가 지키지","천천히, 하지만 확실히"]},
 links:{rank:"인턴",a:"penguin",shirt:"#64748b",tie:"none",acc:["bowtie","badge"],animal:"펭귄",say:["부르셨습니까!","링크 만들어 오겠습니다!"]},
 photo:{rank:"인턴",a:"raccoon",shirt:"#fb7185",tie:"none",acc:["camera","badge"],animal:"라쿤",say:["이 각도가 예뻐요","예쁜 사진만 골라요"]},
 verify:{rank:"인턴",a:"duck",shirt:"#22d3ee",tie:"none",acc:["badge"],animal:"오리",say:["딱 한 번만 눌러볼게요!","두 번은 안 눌러요!"]},
};
// 표정 부품
function eye(x,y,k,dark){
  const W = dark ? "#fff" : "#2b2118";
  if(k==="normal"||k==="surprise"){const r=k==="surprise"?5.2:4.2;return `<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r*1.15}" fill="#2b2118"/><circle cx="${x+1.5}" cy="${y-1.8}" r="${r*.42}" fill="#fff"/><circle cx="${x-1.2}" cy="${y+1.6}" r="${r*.2}" fill="#fff"/>`}
  if(k==="focus") return `<ellipse cx="${x}" cy="${y+1}" rx="3.6" ry="2.6" fill="#2b2118"/><circle cx="${x+1}" cy="${y}" r="1" fill="#fff"/>`;
  if(k==="busy") return `<path d="M${x-5},${y+1} q5,-3 10,0" stroke="${W}" stroke-width="2.6" fill="none" stroke-linecap="round"/>`;
  if(k==="happy") return `<path d="M${x-5},${y+1} q5,-7 10,0" stroke="${W}" stroke-width="2.6" fill="none" stroke-linecap="round"/>`;
  if(k==="sleepy") return `<path d="M${x-5},${y} q5,4 10,0" stroke="${W}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`;
  if(k==="sad") return `<ellipse cx="${x}" cy="${y}" rx="4" ry="4.6" fill="#2b2118"/><circle cx="${x+1.3}" cy="${y-1.6}" r="1.7" fill="#fff"/>`;
  if(k==="excited") return `<path d="M${x},${y-6} l1.8,4 4.3,.4 -3.3,2.8 1,4.2 -3.8,-2.3 -3.8,2.3 1,-4.2 -3.3,-2.8 4.3,-.4Z" fill="#f5b940" stroke="#2b2118" stroke-width=".8"/>`;
  return "";
}
function brows(k,y){
  if(k==="busy") return `<path d="M-15,${y-9} l9,4" stroke="#5b3a2e" stroke-width="2.4" stroke-linecap="round"/><path d="M15,${y-9} l-9,4" stroke="#5b3a2e" stroke-width="2.4" stroke-linecap="round"/>`;
  if(k==="sad") return `<path d="M-15,${y-6} l9,-4" stroke="#5b3a2e" stroke-width="2.2" stroke-linecap="round"/><path d="M15,${y-6} l-9,-4" stroke="#5b3a2e" stroke-width="2.2" stroke-linecap="round"/>`;
  if(k==="focus") return `<path d="M-15,${y-8} l9,1" stroke="#5b3a2e" stroke-width="2" stroke-linecap="round"/><path d="M15,${y-8} l-9,1" stroke="#5b3a2e" stroke-width="2" stroke-linecap="round"/>`;
  return "";
}
function mouth(k,y){
  return {
   normal:`<path d="M-4,${y} q2,3 4,0 q2,3 4,0" stroke="#5b3a2e" stroke-width="1.6" fill="none" stroke-linecap="round"/>`,
   focus:`<path d="M-3,${y+1} h6" stroke="#5b3a2e" stroke-width="1.8" stroke-linecap="round"/>`,
   busy:`<path d="M-5,${y+2} q2.5,-3 5,0 q2.5,3 5,0" stroke="#5b3a2e" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
   happy:`<path d="M-6,${y-1} q6,8 12,0 Z" fill="#c2453a"/>`,
   sleepy:`<ellipse cx="2" cy="${y+1}" rx="2.2" ry="1.6" fill="#5b3a2e"/>`,
   surprise:`<ellipse cx="0" cy="${y+1.5}" rx="3" ry="3.8" fill="#5b3a2e"/>`,
   sad:`<path d="M-5,${y+3} q5,-5 10,0" stroke="#5b3a2e" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
   excited:`<path d="M-7,${y-1} q7,10 14,0 Z" fill="#c2453a"/>`,
  }[k] || "";
}
function extra(k){
  if(k==="busy") return `<path d="M27,-66 q4,7 0,10 q-4,-3 0,-10Z" fill="#7dd3fc"/><text x="-40" y="-70" font-size="13">💢</text>`;
  if(k==="sad") return `<path d="M-13,-42 q-2,8 1,11 q3,-3 -1,-11Z" fill="#7dd3fc"/>`;
  if(k==="sleepy") return `<circle cx="9" cy="-33" r="2.6" fill="#bfe8ff" opacity=".9"/>`;
  if(k==="happy") return `<text x="24" y="-68" font-size="13">✨</text>`;
  if(k==="excited") return `<text x="-42" y="-68" font-size="13">🎉</text><text x="26" y="-68" font-size="13">🎉</text>`;
  if(k==="surprise") return `<text x="24" y="-70" font-size="15" font-weight="900" fill="#f5b940">!</text>`;
  return "";
}
function drawChar(id, k){
  const c = TEAM[id], h = HEAD[c.a], fur = h.fur;
  const tie = c.tie==="wide" ? `<path d="M-5,-27 L5,-27 L3.5,-10 L0,-6 L-3.5,-10Z" fill="#7c2d12"/>` : c.tie==="none" ? "" : `<path d="M-3,-27 L3,-27 L1.5,-14 L0,-11 L-1.5,-14Z" fill="#2b2e3d"/>`;
  const up = k==="excited";
  const arms = up ? `<ellipse cx="-24" cy="-30" rx="5" ry="9" fill="${fur}" transform="rotate(-30 -24 -30)"/><ellipse cx="24" cy="-30" rx="5" ry="9" fill="${fur}" transform="rotate(30 24 -30)"/>`
                  : `<ellipse cx="-20" cy="-16" rx="5" ry="8" fill="${fur}" transform="rotate(20 -20 -16)"/><ellipse class="arm r" cx="20" cy="-16" rx="5" ry="8" fill="${fur}" transform="rotate(-20 20 -16)"/>`;
  const feet = h.feet || fur;
  const dk = h.dark && ["busy","happy","sleepy"].includes(k);
  const blushO = k==="excited"||k==="happy" ? .85 : .5;
  return `${h.tail||""}<ellipse cx="-9" cy="2" rx="7" ry="5" fill="${feet}"/><ellipse cx="9" cy="2" rx="7" ry="5" fill="${feet}"/>${h.shell||""}
   <path d="M-18,-2 Q-22,-26 -12,-28 L12,-28 Q22,-26 18,-2 Q0,4 -18,-2Z" fill="${c.shirt}"/>
   ${c.ai?`<text x="0" y="-9" font-size="9" font-weight="900" text-anchor="middle" fill="#12131a">AI</text>`:tie}
   ${arms}${h.ears}<ellipse cx="0" cy="-50" rx="30" ry="27" fill="${fur}"/>${h.face}
   ${eye(-11,-48,k,dk)}${eye(11,-48,k,dk)}${brows(k,-48)}
   <ellipse cx="-19" cy="-38" rx="5.5" ry="3.2" fill="#ff8fa3" opacity="${blushO}"/><ellipse cx="19" cy="-38" rx="5.5" ry="3.2" fill="#ff8fa3" opacity="${blushO}"/>
   ${h.beak?"":`<ellipse cx="0" cy="-41" rx="3" ry="2.2" fill="#5b3a2e"/>`}${h.beak?"":mouth(k,-36)}
   ${(c.acc||[]).map(a=>ACC[a]).join("")}${extra(k)}`;
}
window.CHAR = { TEAM, drawChar };
})();
