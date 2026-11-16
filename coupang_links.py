# -*- coding: utf-8 -*-
"""
글마다 꼬리표(subId)가 다른 쿠팡파트너스 링크로 바꿔 끼우기 → 어느 글에서 클릭이 났는지 추적
  python coupang_links.py         시험: stats/links.csv 에 새 링크만 만들어 둠 (글은 안 바꿈)
  python coupang_links.py 적용     posts/queue 글 안의 링크를 새 링크로 교체
subId = 파일 이름에서 만든 짧은 영문 (예: 20261117-2200_desk.txt → d1117desk)
"""
import csv
import os
import re
import sys
import urllib.parse
import urllib.request

from coupang_stats import BASE, call

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "posts", "queue")
OUT = os.path.join(HERE, "stats", "links.csv")
SHORT = re.compile(r"https://link\.coupang\.com/a/[A-Za-z0-9]+")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def resolve(short):
    """짧은 링크 → 쿠팡 상품 주소 (파트너 꼬리표는 떼어냄)"""
    opener = urllib.request.build_opener(NoRedirect)
    url = short
    for _ in range(6):
        try:
            r = opener.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
            loc = r.headers.get("Location")
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location")
        if not loc:
            break
        url = urllib.parse.urljoin(url, loc)
        if "coupang.com/vp/products/" in url or "coupang.com/np/" in url:
            break
    u = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(u.query)
    keep = {k: q[k][0] for k in ("itemId", "vendorItemId") if k in q}
    return urllib.parse.urlunparse(("https", "www.coupang.com", u.path, "", urllib.parse.urlencode(keep), ""))


def sub_id(name):
    m = re.match(r"\d{4}(\d{4})-(\d{2})\d{2}_(\w+)\.txt", name)
    if not m:
        return re.sub(r"[^A-Za-z0-9]", "", name)[:20]
    mmdd, hh, slug = m.groups()
    return (("d" if hh == "22" else "l") + mmdd + re.sub(r"[^A-Za-z0-9]", "", slug))[:20]


def main(apply):
    rows, done = [], {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8-sig") as f:
            for r in list(csv.DictReader(f)):
                done[(r["파일"], r["원래링크"])] = r
    for name in sorted(os.listdir(QUEUE)):
        path = os.path.join(QUEUE, name)
        text = open(path, encoding="utf-8").read()
        changed = text
        for short in sorted(set(SHORT.findall(text))):
            key = (name, short)
            if key in done and done[key].get("새링크"):
                new = done[key]["새링크"]
            else:
                sid = sub_id(name)
                try:
                    target = resolve(short)
                    res = call("POST", f"{BASE}/deeplink", body={"coupangUrls": [target], "subId": sid})
                    data = (res.get("data") or [{}])[0]
                    new = data.get("shortenUrl", "")
                    if not new:
                        raise RuntimeError(str(res)[:200])
                except Exception as e:
                    print(f"✗ {name} {short}: {e}")
                    done[key] = {"파일": name, "subId": sid, "원래링크": short, "상품주소": "", "새링크": "", "오류": str(e)[:200]}
                    continue
                done[key] = {"파일": name, "subId": sid, "원래링크": short, "상품주소": target, "새링크": new, "오류": ""}
                print(f"✓ {name} [{sid}] {short} → {new}")
            if apply and new:
                changed = changed.replace(short, new)
        if apply and changed != text:
            open(path, "w", encoding="utf-8").write(changed)
            print(f"  교체함: {name}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["파일", "subId", "원래링크", "상품주소", "새링크", "오류"])
        w.writeheader()
        w.writerows(done.values())


if __name__ == "__main__":
    main(len(sys.argv) > 1 and sys.argv[1] in ("적용", "apply"))
