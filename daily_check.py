# -*- coding: utf-8 -*-
"""부계정 매일 점검 (11/23 Ssuii: "데일리로 조회수 봐서 조회수가 있는데도 클릭이 없다면 의심해보는게 맞을거 같아.
그에 맞는 원인 분석과 조치도 필요해보여. 그 과정에서 뭔가 필요하면 나에게 알려주면 내가 조치할게.")

insights.yml(매일 23:40) 에서 성과·쿠팡 숫자를 모은 뒤 돈다. 토큰(AI) 안 씀.
  1. 어제(KST) 부계정에 올라간 글들의 조회 합 vs 어제 쿠팡 클릭
  2. 조회는 있는데(150 이상) 클릭 0이면 원인 찾기
     a. 글 속 링크가 등록 채널 아이디(ssagesave01·ssageitem01·tenpmblog01)로 만든 건지 (미등록이면 클릭이 안 잡힘)
        → 앞으로 올라갈 글(queue)에 같은 문제가 있으면 links_mode.txt 로 다시 만들기 요청
     b. 링크 1개만 실제로 열어 상품 페이지로 가는지 (3일에 한 번만 — 반복해서 열면 클릭 조작으로 보일 수 있음)
     c. 둘 다 정상이면 "글이 클릭을 못 끌어냄"(형식 문제) → 일요일 리포트가 형식을 고침
  3. 기록: stats/deal/daily_check.csv
  4. 폰 알림(ntfy)은 Ssuii 손이 필요할 때만: 링크 고장인데 자동으로 못 고침 / 3일 연속 '링크 정상인데 클릭 0'
     (이때는 폰으로 부계정 글을 열어 이어쓰기에 링크가 보이는지 한 번 봐 달라고)
"""
import csv, datetime, glob, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REG = {"ssagesave01", "ssageitem01", "tenpmblog01"}
OUT = os.path.join(HERE, "stats", "deal", "daily_check.csv")
LINK = re.compile(r"https://link\.coupang\.com/a/\w+")


def P(*a):
    return os.path.join(HERE, *a)


def rows(path):
    try:
        return list(csv.DictReader(open(path, encoding="utf-8-sig")))
    except FileNotFoundError:
        return []


def good_links():
    ok = set()
    for r in rows(P("stats", "links.csv")):
        if r.get("subId") in REG and r.get("새링크"):
            ok.add(r["새링크"])
    for r in rows(P("stats", "links_made.csv")):
        if r.get("subId") in REG and r.get("링크"):
            ok.add(r["링크"])
    try:
        for v in json.load(open(P("curate", "links.json"), encoding="utf-8")).values():
            if isinstance(v, dict) and v.get("subId") in REG:
                ok.update(x for x in (v.get("link"), v.get("item_link")) if x)
                ok.update(m["item_link"] for m in v.get("more", []) if m.get("item_link"))
    except Exception:
        pass
    for f in glob.glob(P("curate", "links_bio2.json")):
        try:
            ok.update(x for x in json.dumps(json.load(open(f, encoding="utf-8"))).split('"') if x.startswith("https://link.coupang"))
        except Exception:
            pass
    return ok


def gold_or_ok(fn):
    # 골드박스 글은 deal_unit.goldpost 가 ssageitem01 로 바로 만듦 → 등록 링크로 침
    return "_gold" in fn


def opens_product(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return "coupang.com" in r.geturl()
    except Exception as e:
        print("링크 열기 실패", str(e)[:60])
        return False


def notify(title, msg):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        print("알림(보낼 곳 없음):", title, msg)
        return
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=msg.encode("utf-8"),
                                 headers={"Title": title.encode("utf-8"), "Tags": "mag"})
    try:
        urllib.request.urlopen(req, timeout=20)
    except Exception as e:
        print("알림 실패", e)


def main():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    day = now - datetime.timedelta(days=1)
    d_dash, d_num = f"{day:%Y-%m-%d}", f"{day:%Y%m%d}"

    # 어제 올라간 부계정 글
    posted = []
    try:
        for line in open(P("posts", "deal", "posted_log.txt"), encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[0].startswith(d_dash):
                posted.append((p[1], p[2]))
    except FileNotFoundError:
        pass
    views = {}
    for r in rows(P("stats", "deal", "posts.csv")):
        try:
            views[r["글ID"]] = int(r["views"] or 0)
        except (KeyError, ValueError):
            pass
    total_views = sum(views.get(pid, 0) for _, pid in posted)
    links = {}
    for fn, _ in posted:
        f = P("posts", "deal", "done", fn)
        if os.path.exists(f):
            links[fn] = LINK.findall(open(f, encoding="utf-8").read())
    n_link_posts = sum(1 for v in links.values() if v)

    clicks = 0
    for r in rows(P("stats", "coupang_daily.csv")):
        if r.get("날짜") == d_num:
            clicks = int(r.get("클릭") or 0)

    prev = rows(OUT)
    flag, cause, action, opened = "", "", "", ""
    if n_link_posts and total_views >= 150 and clicks == 0:
        flag = "의심"
        ok = good_links()
        bad = [(fn, u) for fn, us in links.items() if not gold_or_ok(fn) for u in us if u not in ok]
        if bad:
            cause = f"미등록 링크 {len(bad)}개 ({bad[0][0]})"
            # 앞으로 올라갈 글도 점검 → 다시 만들기 요청
            q_bad = [f for f in glob.glob(P("posts", "deal", "queue", "*.txt"))
                     if "_gold" not in f and any(u not in ok for u in LINK.findall(open(f, encoding="utf-8").read()))]
            if q_bad:
                open(P("stats", "deal", "relink.flag"), "w").write(d_dash)
                action = f"예약 글 {len(q_bad)}개 링크 다시 만들기"
            else:
                action = "예약 글은 정상"
        else:
            recent = [r for r in prev[-3:] if r.get("실제로 열어봄") == "예"]
            first = next((u for us in links.values() for u in us), None)
            if first and not recent:
                opened = "예"
                if not opens_product(first):
                    cause = "링크를 열었는데 상품 페이지로 안 감"
                    action = "확인 필요"
                    notify("부계정 링크 고장 의심", f"{d_dash} 조회 {total_views}인데 클릭 0. 링크를 열어보니 상품 페이지로 안 감. 쿠팡파트너스 사이트에 로그인해서 공지·계정 상태를 한 번 봐줘.")
            if not cause:
                cause = "링크 정상 → 글이 클릭을 못 끌어냄(형식) 또는 쿠팡 집계 지연"
                action = "일요일 리포트가 형식 조정"
            streak = 1
            for r in reversed(prev):
                if r.get("판정") == "의심" and r.get("원인", "").startswith("링크 정상"):
                    streak += 1
                else:
                    break
            if streak >= 3:
                notify("부계정 3일째 클릭 0", f"조회는 나오는데({total_views}) 클릭이 3일째 0이야. 폰으로 부계정 최근 글을 열어서 이어쓰기(댓글)에 쿠팡 링크가 보이는지 한 번만 봐줘.")
                action += " · 알림 보냄"
        row = {"날짜": d_dash, "글 수": len(posted), "조회 합": total_views, "클릭": clicks, "판정": flag,
               "원인": cause, "조치": action, "실제로 열어봄": opened}
    else:
        row = {"날짜": d_dash, "글 수": len(posted), "조회 합": total_views, "클릭": clicks,
               "판정": "정상" if clicks else ("표본 적음" if posted else "글 없음"), "원인": "", "조치": "", "실제로 열어봄": ""}

    if any(r.get("날짜") == d_dash for r in prev):
        print("이미 기록됨", d_dash)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    new = not os.path.exists(OUT)
    with open(OUT, "a", encoding="utf-8-sig" if new else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print("부계정 점검", row)


if __name__ == "__main__":
    main()
