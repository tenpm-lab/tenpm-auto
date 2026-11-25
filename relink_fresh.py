"""부계정 queue 링크를 저장해둔 상품 주소로 새로 만들기 (링크를 열지 않음).
11/26: 채널 아이디 승인 전에 만든 링크는 안 잡힐 수 있다는 댓글 → 승인 뒤(지금) 다시 만들어 교체.
사용: ACCOUNT=deal python relink_fresh.py"""
import csv, datetime, glob, os, re
from coupang_links import call, BASE, REG

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "stats", "links.csv"), encoding="utf-8-sig")))
by = {r["새링크"]: r for r in rows if r.get("새링크") and r.get("상품주소") and r.get("subId") in REG}
made = open(os.path.join(HERE, "stats", "links_made.csv"), "a", encoding="utf-8")
today = f"{datetime.date.today():%Y%m%d}"
n = 0
for path in sorted(glob.glob(os.path.join(HERE, "posts", "deal", "queue", "*.txt"))):
    text = open(path, encoding="utf-8").read()
    new_text = text
    for old in sorted(set(re.findall(r"https://link\.coupang\.com/a/\w+", text))):
        r = by.get(old)
        if not r:
            continue
        res = call("POST", f"{BASE}/deeplink", body={"coupangUrls": [r["상품주소"]], "subId": r["subId"]})
        new = ((res.get("data") or [{}])[0]).get("shortenUrl", "")
        if not new:
            print("✗", os.path.basename(path), str(res)[:120])
            continue
        new_text = new_text.replace(old, new)
        rows.append({"파일": os.path.basename(path), "subId": r["subId"], "원래링크": old, "상품주소": r["상품주소"], "새링크": new, "오류": ""})
        made.write(f"{today},{r['subId']},{new}\n")
        n += 1
    if new_text != text:
        open(path, "w", encoding="utf-8").write(new_text)
        print("교체", os.path.basename(path))
with open(os.path.join(HERE, "stats", "links.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["파일", "subId", "원래링크", "상품주소", "새링크", "오류"])
    w.writeheader()
    w.writerows(rows)
print("새로 만든 링크", n)
