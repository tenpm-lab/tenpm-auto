# -*- coding: utf-8 -*-
"""
쓰레드 장기 토큰 자동 연장 (매달 1일·15일 GitHub에서 실행)
1) 지금 토큰으로 새 60일 토큰을 받음 (쓰레드 공식 refresh_access_token)
2) GitHub 비밀값 THREADS_TOKEN 을 새 토큰으로 교체 (GH_SECRETS_PAT 필요: 이 저장소 Secrets 읽기/쓰기 권한)
토큰 값은 어디에도 출력하지 않는다.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
REPO = os.environ.get("GITHUB_REPOSITORY", "tenpm-lab/tenpm-auto")


def notify(title, msg):
    t = os.environ.get("NTFY_TOPIC", "").strip()
    if not t:
        return
    try:
        urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + t, data=msg.encode(),
            headers={"Title": title.encode(), "Tags": "key"}, method="POST"), timeout=20).read()
    except Exception as e:
        print("알림 실패:", e)


def gh(method, path, body=None):
    pat = os.environ["GH_SECRETS_PAT"].strip()
    req = urllib.request.Request("https://api.github.com" + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + pat, "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else {}


def fail(msg):
    print("❌", msg)
    notify("⚠️ 쓰레드 토큰 연장 실패", msg[:120] + "\nAI 대화창에 '토큰 연장 실패'라고 보내줘")
    sys.exit(1)


def main():
    SECRET = os.environ.get("SECRET_NAME", "THREADS_TOKEN").strip()
    old = os.environ.get("THREADS_TOKEN", "").strip()
    if not old:
        if SECRET != "THREADS_TOKEN":
            print("부계정 토큰 없음 - 건너뜀"); return
        fail("THREADS_TOKEN 없음")
    if not os.environ.get("GH_SECRETS_PAT", "").strip():
        fail("GH_SECRETS_PAT 없음 (GitHub 비밀값에 넣어야 함)")

    # 1) 새 토큰 받기
    q = urllib.parse.urlencode({"grant_type": "th_refresh_token", "access_token": old})
    try:
        with urllib.request.urlopen("https://graph.threads.net/refresh_access_token?" + q, timeout=30) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        fail(f"쓰레드 연장 거절 ({e.code}): {body[:200]}")
    new, sec = res.get("access_token", ""), int(res.get("expires_in", 0))
    if not new:
        fail("새 토큰이 안 옴")
    until = datetime.now(KST) + timedelta(seconds=sec)

    # 2) GitHub 비밀값 교체 (공개키로 암호화)
    try:
        from nacl import encoding, public
    except ImportError:
        fail("PyNaCl 설치 안 됨")
    try:
        key = gh("GET", f"/repos/{REPO}/actions/secrets/public-key")
        box = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder()))
        enc = base64.b64encode(box.encrypt(new.encode())).decode()
        gh("PUT", f"/repos/{REPO}/actions/secrets/" + SECRET, {"encrypted_value": enc, "key_id": key["key_id"]})
    except urllib.error.HTTPError as e:
        fail(f"GitHub 비밀값 교체 실패 ({e.code}) — GH_SECRETS_PAT 권한 확인")

    msg = f"새 토큰 만료 예정: {until:%Y-%m-%d} (다음 연장은 자동)"
    print("✅", msg)
    notify("🔑 쓰레드 토큰 연장 완료", msg)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "posts", "token_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(KST):%Y-%m-%d %H:%M}\t{SECRET} 연장 성공\t만료 {until:%Y-%m-%d}\n")


if __name__ == "__main__":
    main()
