# -*- coding: utf-8 -*-
"""links_check.txt 의 "번호 링크" 줄마다 쿠팡 짧은 링크가 상품 페이지로 잘 가는지 확인 → stats/link_check.txt"""
import os, re, datetime, urllib.request, urllib.error, urllib.parse

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None

def follow(url):
    op = urllib.request.build_opener(NoRedirect)
    hops = []
    for _ in range(6):
        try:
            r = op.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
            code, loc = r.status, r.headers.get("Location")
        except urllib.error.HTTPError as e:
            code, loc = e.code, e.headers.get("Location")
        hops.append(code)
        if not loc:
            break
        url = urllib.parse.urljoin(url, loc)
        if "/vp/products/" in url:
            break
    return url, hops

out = []
for line in open("links_check.txt", encoding="utf-8"):
    m = re.match(r"\s*(\S+)\s+(https://link\.coupang\.com/a/\w+)", line)
    if not m:
        continue
    no, short = m.groups()
    try:
        final, hops = follow(short)
        u = urllib.parse.urlparse(final)
        q = urllib.parse.parse_qs(u.query)
        pid = re.search(r"/vp/products/(\d+)", u.path)
        ok = "정상" if pid else "확인 필요"
        out.append(f"{no}\t{ok}\t상품번호 {pid.group(1) if pid else '-'}\titemId {q.get('itemId',['-'])[0]}\t{short}")
    except Exception as e:
        out.append(f"{no}\t오류\t{str(e)[:80]}\t{short}")
os.makedirs("stats", exist_ok=True)
open("stats/link_check.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))


def _log_bot(n, reason="링크 확인(check_links.py)"):
    """우리 프로그램이 쿠팡 링크를 열어본 횟수 기록 (쿠팡 리포트 클릭에 섞일 수 있어서 나중에 빼고 보려고)"""
    import datetime as _d, os as _o
    if n <= 0:
        return
    p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "stats", "bot_clicks.csv")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{_d.datetime.now(_d.timezone(_d.timedelta(hours=9))):%Y-%m-%d},{n},{reason}\n")

_log_bot(len(out))
