# -*- coding: utf-8 -*-
"""문서용 마크다운 출력.
  python threads_table.py main > /tmp/main.md   # '쓰레드 글' 탭: 한눈에 보기 + 올릴 글 표 + 올릴 글 본문
  python threads_table.py done > /tmp/done.md   # '올린 글' 하위 탭: 올린 글 표 + 올린 글 본문
"""
import csv, glob, os, collections, datetime, sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "main"
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, *a)
FENCE = "`" * 3

stats = {}
if os.path.exists(P("stats", "posts.csv")):
    for r in csv.DictReader(open(P("stats", "posts.csv"), encoding="utf-8-sig")):
        stats[r["첫줄"].strip()] = r


def parse(f):
    topic, body = "", []
    for l in open(f, encoding="utf-8").read().split("\n---")[0].splitlines():
        if l.startswith("주제:"):
            topic = l[3:].strip(); continue
        if l.startswith(("사진:", "영상:")):
            continue
        if l.strip():
            body.append(l.strip())
    return topic, (body[0] if body else "")


def body(path):
    parts = open(path, encoding="utf-8").read().split("\n---")
    lines = [l for l in parts[0].splitlines() if not l.startswith(("주제:", "사진:", "영상:"))]
    out = "\n".join(lines).strip()
    for extra in parts[1:]:
        out += "\n\n— 이어 쓰기 —\n" + extra.strip()
    return out.replace(FENCE, "'''")


def cat(fn, topic, first):
    if "_save_" in fn: return "💰 싸게 사는 법"
    if "(광고)" in first: return "🛒 상품"
    if "_am_" in fn: return "☀️ 아침 공감"
    if "weekly" in fn or first.startswith("[AI한테"): return "📈 주간 정리"
    if "_info_" in fn or "방법 있는 거 앎" in first or "시작한 거 앎" in first or "정부 사이트" in first: return "📌 정보"
    if "부업" in topic or "money" in fn or "쿠팡파트너스" in first or "돈" in first: return "💸 돈·부업 정보"
    if "꿀팁" in topic or "정보" in topic: return "📌 정보"
    return "💬 공감·대화"


def esc(s): return s.replace("|", "/")[:48]
def d(fn): return f"{fn[4:6]}/{fn[6:8]} {fn[9:11]}:{fn[11:13]}"


done, q = [], []
for f in sorted(glob.glob(P("posts", "done", "*.txt"))):
    fn = os.path.basename(f); topic, first = parse(f)
    if first and not first.startswith("[1/"):
        done.append((f, fn, cat(fn, topic, first), first, stats.get(first)))
for f in sorted(glob.glob(P("posts", "queue", "*.txt"))):
    fn = os.path.basename(f); topic, first = parse(f)
    q.append((f, fn, cat(fn, topic, first), first))

today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%m/%d")

if MODE == "main":
    agg, cnt = collections.defaultdict(list), collections.Counter()
    for f, fn, c, first, s in done:
        cnt[c] += 1
        if s: agg[c].append((int(s["views"] or 0), first))
    print(f"## 📊 한눈에 보기 ({today} 기준)\n")
    print("| 카테고리 | 올린 글 | 평균 조회 | 제일 잘 된 글 |\n|---|---|---|---|")
    for c in sorted(cnt, key=lambda c: -(sum(a for a, _ in agg[c]) / len(agg[c]) if agg[c] else 0)):
        v = agg[c]
        if v:
            b = max(v); print(f"| {c} | {cnt[c]} | {round(sum(a for a, _ in v) / len(v)):,} | {esc(b[1])} ({b[0]:,}) |")
        else:
            print(f"| {c} | {cnt[c]} | - | - |")
    print("\n카테고리: 📌 정보 / 💸 돈·부업 정보 / 💰 싸게 사는 법(쿠팡 링크) / 🛒 상품(쿠팡 링크) / ☀️ 아침 공감 / 💬 공감·대화 / 📈 주간 정리. 조회는 매일 아침 자동 수집 기준. 올라간 글은 '올린 글' 하위 탭에.")
    print("\n## 📅 올릴 글 (예약)\n")
    print("| 날짜 | 카테고리 | 첫 줄 |\n|---|---|---|")
    for f, fn, c, first in q: print(f"| {d(fn)} | {c} | {esc(first)} |")
    print("\n## 📝 올릴 글 본문\n")
    for f, fn, c, first in q:
        print(f"### {d(fn)} · {c}\n\n{FENCE}\n{body(f)}\n{FENCE}\n")
else:
    print(f"## ✅ 올린 글 ({today} 기준, 최신순)\n")
    print("| 날짜 | 카테고리 | 첫 줄 | 조회 | 공유 |\n|---|---|---|---|---|")
    for f, fn, c, first, s in reversed(done):
        print(f"| {d(fn)} | {c} | {esc(first)} | {int(s['views'] or 0):,} | {s['shares']} |" if s else f"| {d(fn)} | {c} | {esc(first)} | - | - |")
    print("\n## 📝 올린 글 본문 (최신순)\n")
    for f, fn, c, first, s in reversed(done):
        v = f" · 조회 {int(s['views'] or 0):,}" if s else ""
        print(f"### {d(fn)} · {c}{v}\n\n{FENCE}\n{body(f)}\n{FENCE}\n")
