"""AI 사무실: 직원별 '최근에 한 일'을 저장소 기록에서 뽑아 office/status.json 으로.
실시간 상태(일하는 중/문제)는 사무실 페이지가 GitHub 실행 기록을 직접 읽어요. 여기서는 내용만.
내용이 바뀌었을 때만 파일을 새로 써요 (15분마다 기록이 쌓이지 않게)."""
import glob, json, os, datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
TODAY = NOW.strftime("%Y-%m-%d")
OUT = os.path.join(HERE, "office", "status.json")
# 파일 이름에 들어간 말로 글 종류 표시 (예: 20261201-2030_story_xxx.txt → 경험 글). 마음대로 추가하세요.
KIND = [("_story_", "경험 글"), ("_info_", "정보 글"), ("_ask_", "질문 글"), ("_list_", "목록 글"), ("_tech_", "테크 소식")]


def p(*a):
    return os.path.join(HERE, *a)


def lines(path):
    try:
        return [l.rstrip("\n") for l in open(path, encoding="utf-8-sig") if l.strip()]
    except FileNotFoundError:
        return []


def kind(name):
    return next((v for k, v in KIND if k in name), "글")


def main():
    log = lines(p("posts", "posted_log.txt"))
    today = sum(1 for l in log if l.startswith(TODAY))
    if log:
        t, name = log[-1].split("\t")[:2]
        did = f"{t[5:].replace('-', '/')} {kind(name)} 올림"
    else:
        did = "아직 기록 없음"
    queue = sorted(os.path.basename(f) for f in glob.glob(p("posts", "queue", "*.txt")))
    plan = []
    for b in queue[:8]:
        title = next((l.strip()[:34] for l in lines(p("posts", "queue", b))
                      if not l.startswith(("주제:", "사진:")) and l.strip() != "---"), "")
        plan.append(dict(when=f"{b[4:6]}/{b[6:8]} {b[9:11]}:{b[11:13]}", kind=kind(b), title=title))
    rep = lines(p("stats", "replied.txt"))
    fol = lines(p("stats", "followers.csv"))
    fnum = fol[-1].split(",")[1] if len(fol) > 1 else "?"
    tok = lines(p("posts", "token_log.txt"))
    staff = [
        dict(id="poster", name="게시 담당", role="예약한 글 올리기", wf="post.yml", when="15분마다", did=did,
             note=(f"다음: {plan[0]['when']} {plan[0]['kind']}" if plan else "예약 글 없음"), count=f"오늘 {today}개 · 대기 {len(queue)}개"),
        dict(id="reply", name="댓글 담당", role="정해둔 댓글에 답장", wf="post.yml", when="15분마다",
             did=f"지금까지 답장 {len(rep)}개", note="" if rep else "댓글 기다리는 중", count=""),
        dict(id="stats", name="통계 담당", role="팔로워 수 기록", wf="post.yml", when="15분마다", did=f"팔로워 {fnum}명 기록", note="", count=""),
        dict(id="key", name="열쇠 담당", role="토큰 연장", wf="token.yml", when="매달 1일·15일",
             did=(tok[-1].split("\t")[-1] if tok else "첫 연장 기다리는 중"), note="", count=""),
    ]
    top = dict(followers=fnum, posts_total=len(log), clicks=0, earn=0, today=today,
               next=(plan[0]["when"][-5:] if plan else ""), deal_queue=0)
    data = dict(top=top, staff=staff, waiting=[], plan=plan)
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8")); old.pop("updated", None)
    if old != data:
        data["updated"] = NOW.strftime("%Y-%m-%d %H:%M")
        json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("사무실 상태 갱신")
    else:
        print("변화 없음")


if __name__ == "__main__":
    main()
