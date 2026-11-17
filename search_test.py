# 쓰레드 키워드 검색 권한 테스트 (결과 개수와 오류만 출력)
import json, os, urllib.parse, urllib.request
T = os.environ["THREADS_TOKEN"]
def get(path, **q):
    q["access_token"] = T
    url = "https://graph.threads.net/v1.0/" + path + "?" + urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read().decode() or "{}").get("error", {})}
for kw in ["육아템", "직장인 간식"]:
    for st in ["TOP", "RECENT"]:
        r = get("keyword_search", q=kw, search_type=st, fields="id,username,timestamp,permalink,text")
        if "error" in r:
            e = r["error"]; print(f"[{kw}/{st}] 오류 code={e.get('code')} {e.get('message','')[:150]}")
        else:
            d = r.get("data", [])
            print(f"[{kw}/{st}] {len(d)}개 · 예: " + ", ".join(f"@{x.get('username')} {x.get('timestamp','')[:10]}" for x in d[:3]))
me = get("me", fields="id,username")
print("내 계정 확인:", "ok" if "id" in me else me)
