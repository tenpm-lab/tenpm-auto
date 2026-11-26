"""AI 직원 사무실: 직원별 '최근에 한 일'을 저장소 기록에서 뽑아 office/status.json 으로.
실시간 상태(일하는 중/문제)는 페이지가 GitHub 실행 기록을 직접 읽음. 여기서는 내용만.
내용이 바뀌었을 때만 파일을 새로 씀 (15분마다 커밋 쌓이지 않게)."""
import csv, datetime, glob, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
TODAY = NOW.strftime("%Y-%m-%d")
OUT = os.path.join(HERE, "office", "status.json")

KIND = [("_tech_", "테크 소식"), ("_story_", "경험 글"), ("_side_", "부수입 목록"), ("_money_", "부수입 글"),
        ("_result_", "결과 공유"), ("_ask_", "질문 글"), ("weekly", "주간 정리"), ("_list_", "목록 글"),
        ("_info_", "정보 글"), ("_talk_", "대화 글"), ("_gold_", "골드박스"), ("_find_", "신기한 물건"),
        ("_save_", "싸게 사는 법"), ("_reply_", "댓글 답 글")]


def p(*a):
    return os.path.join(HERE, *a)


def lines(path):
    try:
        return [l.rstrip("\n") for l in open(path, encoding="utf-8-sig") if l.strip()]
    except FileNotFoundError:
        return []


def kind(name):
    for k, v in KIND:
        if k in name:
            return v
    return "글"


def last_post(log):
    ls = lines(log)
    if not ls:
        return None, 0
    t, name = ls[-1].split("\t")[:2]
    today = sum(1 for l in ls if l.startswith(TODAY))
    return f"{t[5:].replace('-', '/')} {kind(name)} 올림", today


def next_in_queue(folder):
    fs = sorted(os.path.basename(f) for f in glob.glob(p(folder, "*.txt")))
    if not fs:
        return None
    f = fs[0]
    return f"다음: {f[4:6]}/{f[6:8]} {f[9:11]}:{f[11:13]} {kind(f)}", len(fs)


def plan_text(line):
    """info_log 마지막 줄 → '11/26 · AI 정보 #5 제미나이 GIF 초안' 처럼 짧게"""
    if "|" not in line:
        return "아직 기록 없음"
    parts = [x.strip() for x in line.split("|")]
    day = parts[0][5:10].replace("-", "/") if parts[0][:4].isdigit() else ""
    body = parts[-1].split(",")[0].replace("블로그 D ", "").split("(")[0].strip()
    return f"{day} · {body} 초안".strip(" ·")


def main():
    emp = []
    lp, today = last_post(p("posts", "posted_log.txt"))
    nq = next_in_queue("posts/queue")
    emp.append(dict(id="poster", name="게시 담당", role="본계정 글 올리기", wf="post.yml", when="15분마다",
                    did=lp or "아직 기록 없음", note=(nq[0] if nq else "예약 글 없음"), count=f"오늘 {today}개 · 대기 {nq[1] if nq else 0}개"))
    lp2, today2 = last_post(p("posts", "deal", "posted_log.txt"))
    nq2 = next_in_queue("posts/deal/queue")
    emp.append(dict(id="deal", name="부계정 점장", role="쿠팡 전용 계정 운영", wf="post.yml", when="15분마다",
                    did=lp2 or "아직 기록 없음", note=(nq2[0] if nq2 else "예약 글 없음"), count=f"오늘 {today2}개 · 대기 {nq2[1] if nq2 else 0}개"))
    rep = lines(p("stats", "deal", "replied.txt"))
    emp.append(dict(id="reply", name="댓글 담당", role="링크 묻는 댓글에 답장", wf="post.yml", when="15분마다",
                    did=f"지금까지 답장 {len(rep)}개", note="\"어디서 사요?\" 댓글 기다리는 중" if not rep else "", count=""))
    gold = sorted(glob.glob(p("posts", "deal", "*", "*_gold_*.txt")))
    g = os.path.basename(gold[-1]) if gold else ""
    emp.append(dict(id="gold", name="골드박스 담당", role="오늘의 특가 골라 글 쓰기", wf="goldbox.yml", when="매일 08:10",
                    did=(f"{g[4:6]}/{g[6:8]} 특가 글 준비 ({'부르기' if 'call' in g else '가격 맞히기'})" if g else "11/26부터 출근"), note="", count=""))
    fol = lines(p("stats", "followers.csv"))
    fnum = fol[-1].split(",")[1] if fol else "?"
    emp.append(dict(id="stats", name="통계 담당", role="조회·팔로워·쿠팡 클릭 모으기", wf="insights.yml", when="매일 23:40",
                    did=f"팔로워 {fnum}명 기록", note="", count=""))
    dc = lines(p("stats", "deal", "daily_check.csv"))
    if dc:
        c = dc[-1].split(",")
        did = f"{c[0][5:].replace('-', '/')} 점검: 글 {c[1]}개 · 조회 {c[2]} · 클릭 {c[3]} → {c[4]}"
    else:
        did = "아직 기록 없음"
    emp.append(dict(id="check", name="점검 담당", role="클릭 0이면 원인 찾고 고치기", wf="insights.yml", when="매일 23:40",
                    did=did, note="", count=""))
    wk = sorted(glob.glob(p("stats", "weekly", "*.md")))
    emp.append(dict(id="weekly", name="집계 담당", role="주간 숫자 정리", wf="weekly.yml", when="일요일 19:00",
                    did=(f"{os.path.basename(wk[-1])[5:10].replace('-', '/')} 주간 집계" if wk else "아직 기록 없음"), note="", count=""))
    emp.append(dict(id="key", name="열쇠 담당", role="토큰 연장 (본계정·부계정)", wf="token.yml", when="매달 1일·15일",
                    did="두 계정 열쇠 관리", note="", count=""))
    info = lines(p("posts", "info_log.txt"))
    last_plan = info[-1] if info else ""
    emp.append(dict(id="planner", name="기획실장", role="다음 날 글·블로그 초안 (Claude)", wf="", when="평일 16:47",
                    did=plan_text(last_plan), note="", count="", ai=True))
    emp.append(dict(id="editor", name="편집장", role="주간 분석·다음 주 세팅·책 원고 (Claude)", wf="", when="일요일 19:23",
                    did=(f"{os.path.basename(wk[-1])[5:10].replace('-', '/')} 주간 리포트" if wk else "아직 기록 없음"), note="", count="", ai=True))
    wait = [dict(id="links", name="링크 담당", role="쿠팡 링크 만들기", wf="links.yml"),
            dict(id="photo", name="사진 담당", role="상품 사진 고르기", wf="deal.yml"),
            dict(id="verify", name="확인 담당", role="링크 한 번 열어보기", wf="check_links.yml")]
    cd = lines(p("stats", "coupang_daily.csv"))[1:]
    clicks = sum(int(r.split(",")[1] or 0) for r in cd)
    earn = sum(int(r.split(",")[4] or 0) for r in cd)
    top = dict(followers=fnum, posts_total=len(lines(p("posts", "posted_log.txt"))) + len(lines(p("posts", "deal", "posted_log.txt"))),
               clicks=clicks, earn=earn)
    data = dict(top=top, staff=emp, waiting=wait)
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8"))
        old.pop("updated", None)
    if old != data:
        data["updated"] = NOW.strftime("%Y-%m-%d %H:%M")
        json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("사무실 상태 갱신")
    else:
        print("변화 없음")


if __name__ == "__main__":
    main()
