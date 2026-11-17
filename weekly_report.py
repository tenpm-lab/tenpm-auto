# -*- coding: utf-8 -*-
"""
주간 리포트 (매주 일요일 밤 GitHub에서 실행) → stats/weekly/YYYY-MM-DD.md
쓰레드 성과(posts.csv) + 팔로워(account.csv) + 쿠팡 글별 클릭(coupang_by_post.csv) + 게시 기록(posted_log.txt)을
글 종류(정보·공감·상품·주간정리)별로 묶어서 비교한다.
"""
import csv
import os
import re
import sys
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "stats")


def rows(name):
    p = os.path.join(S, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def kind(fname):
    if "_info_" in fname:
        return "정보"
    if "_money_" in fname:
        return "부업정보"
    if "_list_" in fname:
        return "목록"
    if "_am_" in fname:
        return "아침한줄"
    if "_talk_" in fname:
        return "공감"
    if "weekly" in fname:
        return "주간정리"
    if "_bf_" in fname:
        return "상품묶음"
    if "-2200_" in fname:
        return "상품"
    return "기타"


def sub_id(name):
    m = re.match(r"\d{4}(\d{4})-(\d{2})\d{2}_(\w+)\.txt", name)
    if not m:
        return ""
    mmdd, hh, slug = m.groups()
    return (("d" if hh == "22" else "l") + mmdd + re.sub(r"[^A-Za-z0-9]", "", slug))[:20]


def main():
    now = datetime.now(KST)
    start = (now - timedelta(days=6)).strftime("%Y-%m-%d")

    # 게시 기록: 첫 글 ID → 파일 이름
    id2file = {}
    with open(os.path.join(HERE, "posts", "posted_log.txt"), encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2]:
                id2file[p[2].split(",")[0]] = (p[0], p[1])

    # 글별 최신 성과
    latest = {}
    for r in rows("posts.csv"):
        latest[r["글ID"]] = r
    clicks = {r["subId(글)"]: r for r in rows("coupang_by_post.csv")}

    table = []
    for pid, r in latest.items():
        when, fname = id2file.get(pid, (r["올린시각(UTC)"], ""))
        if when[:10] < start:
            continue
        k = kind(fname) if fname else "기타"
        sid = sub_id(fname) if k in ("상품", "상품묶음") else ""
        c = clicks.get(sid, {})
        table.append({
            "when": when, "kind": k, "first": r["첫줄"][:30],
            "views": int(r["views"] or 0), "likes": int(r["likes"] or 0), "replies": int(r["replies"] or 0),
            "reposts": int(r["reposts"] or 0), "shares": int(r["shares"] or 0),
            "clicks": int(list(c.values())[1]) if c else ("-" if not sid else 0), "link": r["링크"]})
    table.sort(key=lambda x: x["when"])

    acc = rows("account.csv")
    f_now = acc[-1]["팔로워"] if acc else "?"
    f_then = next((a["팔로워"] for a in acc if a["수집시각"][:10] >= start), f_now)

    out = [f"# 주간 리포트 {start} ~ {now:%Y-%m-%d}", "",
           f"- 팔로워: {f_then} → {f_now}",
           f"- 이번 주 글 {len(table)}개 · 총 조회 {sum(t['views'] for t in table):,} · 공유 {sum(t['shares'] for t in table)}",
           ""]
    out += ["## 종류별 평균", "", "| 종류 | 글 수 | 평균 조회 | 평균 공유 | 평균 댓글 | 쿠팡 클릭 합 |", "|---|---|---|---|---|---|"]
    kinds = {}
    for t in table:
        kinds.setdefault(t["kind"], []).append(t)
    for k, ts in sorted(kinds.items(), key=lambda x: -sum(t["views"] for t in x[1]) / len(x[1])):
        n = len(ts)
        ck = sum(t["clicks"] for t in ts if isinstance(t["clicks"], int))
        out.append(f"| {k} | {n} | {sum(t['views'] for t in ts)//n:,} | {sum(t['shares'] for t in ts)/n:.1f} | "
                   f"{sum(t['replies'] for t in ts)/n:.1f} | {ck if k in ('상품','상품묶음') else '-'} |")
    out += ["", "## 글별 (조회 많은 순)", "", "| 날짜 | 종류 | 첫 줄 | 조회 | 좋아요 | 댓글 | 리포스트 | 공유 | 쿠팡 클릭 |", "|---|---|---|---|---|---|---|---|---|"]
    for t in sorted(table, key=lambda x: -x["views"]):
        out.append(f"| {t['when'][5:16]} | {t['kind']} | [{t['first']}]({t['link']}) | {t['views']:,} | {t['likes']} | "
                   f"{t['replies']} | {t['reposts']} | {t['shares']} | {t['clicks']} |")
    hub = clicks.get("bio", {})
    out += ["", f"모음 페이지(프로필·상품 글 댓글 링크)에서 쿠팡으로 간 클릭(최근 14일): {list(hub.values())[1] if hub else 0}"]
    untagged = clicks.get("(꼬리표 없음)", {})
    if untagged:
        out += ["", f"꼬리표 없는 예전 링크 클릭(최근 14일): {list(untagged.values())[1]}"]
    bots = [b for b in rows("bot_clicks.csv") if b["날짜"] >= start]
    if bots:
        out += [f"참고: 이번 주 우리 프로그램이 쿠팡 링크를 열어본 횟수 {sum(int(b['횟수']) for b in bots)}번 (쿠팡 클릭에 섞였을 수 있음, 빼고 볼 것)"]
    daily = rows("coupang_daily.csv")
    wk = [d for d in daily if d["날짜"] >= start.replace("-", "")]
    if wk:
        out += [f"쿠팡 이번 주: 클릭 {sum(int(d['클릭']) for d in wk)} · 주문 {sum(int(d['주문']) for d in wk)} · 수익 {sum(int(d['수익']) for d in wk):,}원"]

    # 팔로워가 늘어난 시각 → 그 직전 6시간 안에 올라간 글 (11/17~)
    fl = rows("followers.csv")
    gains = []
    for a, b in zip(fl, fl[1:]):
        d = int(b["팔로워"]) - int(a["팔로워"])
        if d > 0 and b["시각(KST)"][:10] >= start:
            t = datetime.strptime(b["시각(KST)"], "%Y-%m-%d %H:%M")
            before = [x for x in table if x["when"][:16] and t - timedelta(hours=6) <= datetime.strptime(x["when"][:16], "%Y-%m-%d %H:%M") <= t]
            near = max(before, key=lambda x: x["when"]) if before else None
            gains.append(f"| {b['시각(KST)'][5:]} | +{d} | " + (f"{near['kind']} · {near['first']}" if near else "-") + " |")
    if gains:
        out += ["", "## 팔로워가 늘어난 때 (직전 6시간 안에 올라간 글)", "", "| 시각 | 증가 | 직전 글 |", "|---|---|---|"] + gains
    os.makedirs(os.path.join(S, "weekly"), exist_ok=True)
    path = os.path.join(S, "weekly", f"{now:%Y-%m-%d}.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
