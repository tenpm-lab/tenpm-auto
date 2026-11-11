# -*- coding: utf-8 -*-
"""
tenpm.lab 쓰레드 예약 게시 프로그램 (2차 버전, GitHub Actions용)

폴더 구조
  posts/queue/   올릴 글 파일을 넣는 곳
  posts/done/    다 올린 글이 자동으로 옮겨지는 곳
  images/        사진을 넣는 곳

글 파일 이름 = 올릴 날짜와 시간 (한국 시간)
  20261111-2200_장패드.txt   -> 2026년 11월 11일 밤 10시에 올라감

글 파일 내용
  - --- 로 나누면 그 아래 글은 이어 쓰기로 올라감
  - 각 글 맨 위에 "주제: 데스크테리어" 를 쓰면 쓰레드 주제 태그가 붙음
  - 각 글 맨 첫 줄에 "사진: a.jpg, b.jpg" 를 쓰면 images 폴더의 사진이 같이 올라감
    (영상 .mp4/.mov 도 같은 줄에 섞어 쓸 수 있음)
    (사진 1장 = 사진 글, 2장 이상 = 여러 장 넘겨보기 글, 최대 20장)

사용법
  GitHub에서는 15분마다 자동 실행됨. 시간이 된 글만 올라감
  노트북에서 확인용:  python post_queue.py 미리보기
"""

import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.threads.net/v1.0"
KST = timezone(timedelta(hours=9))
HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "posts", "queue")
DONE = os.path.join(HERE, "posts", "done")
IMAGES = os.path.join(HERE, "images")
LOG = os.path.join(HERE, "posts", "posted_log.txt")


# ---------- 설정 ----------
def read_token():
    token = os.environ.get("THREADS_TOKEN", "").strip()
    if token:
        return token
    env_path = os.path.join(HERE, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("THREADS_TOKEN="):
                    return line.split("=", 1)[1].strip()
    sys.exit("토큰이 없어요. GitHub 비밀값(THREADS_TOKEN)이나 .env 파일을 확인해주세요.")


def image_base_url():
    repo = os.environ.get("GITHUB_REPOSITORY", "")  # 예: tenpm-lab/tenpm-auto
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        repo = os.environ.get("TENPM_REPO", "")
    if not repo:
        return None
    return f"https://raw.githubusercontent.com/{repo}/{branch}/images/"


# ---------- API ----------
def call(method, path, params):
    url = API + path
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"쓰레드 API 오류 ({e.code}): {body}")


def wait_ready(token, container_id):
    """사진은 쓰레드가 가져가서 처리할 시간이 필요하다. 준비될 때까지 기다린다."""
    for _ in range(60):  # 최대 약 5분 (영상은 오래 걸림)
        res = call("GET", f"/{container_id}", {"fields": "status,error_message", "access_token": token})
        status = res.get("status")
        if status not in ("FINISHED", "PUBLISHED"):
            print(f"   · 준비 중 {container_id}: {status} {res.get('error_message', '')}")
        if status in (None, "FINISHED", "PUBLISHED"):
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"쓰레드가 글을 준비하지 못했어요: {res.get('error_message', status)}")
        time.sleep(5)
    raise RuntimeError("쓰레드가 글을 준비하는 데 너무 오래 걸려요. 사진 주소를 확인해주세요.")


VIDEO_EXT = (".mp4", ".mov")


def media_params(name, base):
    """사진이면 IMAGE, 영상(.mp4/.mov)이면 VIDEO"""
    url = base + urllib.parse.quote(name)
    if name.lower().endswith(VIDEO_EXT):
        return {"media_type": "VIDEO", "video_url": url}
    return {"media_type": "IMAGE", "image_url": url}


def publish(token, user_id, text, photos, reply_to, base, topic=""):
    params = {"access_token": token, "text": text}
    if topic:
        params["topic_tag"] = topic
    if reply_to:
        params["reply_to_id"] = reply_to

    if not photos:
        params["media_type"] = "TEXT"
    elif len(photos) == 1:
        params.update(media_params(photos[0], base))
    else:
        children = []
        for name in photos:
            item_params = {"access_token": token, "is_carousel_item": "true"}
            item_params.update(media_params(name, base))
            item = call("POST", f"/{user_id}/threads", item_params)
            wait_ready(token, item["id"])
            print(f"   · 사진 준비됨: {name} -> {item['id']}")
            children.append(item["id"])
        params["media_type"] = "CAROUSEL"
        params["children"] = ",".join(children)

    try:
        container = call("POST", f"/{user_id}/threads", params)
    except RuntimeError as e:
        if "topic_tag" not in params:
            raise
        # 주제 태그 때문에 거절되면 태그 없이 한 번 더 시도 (글은 꼭 올라가게)
        print(f"   ⚠️ 주제 태그 없이 다시 올림: {e}")
        params.pop("topic_tag")
        container = call("POST", f"/{user_id}/threads", params)
    wait_ready(token, container["id"])
    result = call("POST", f"/{user_id}/threads_publish",
                  {"creation_id": container["id"], "access_token": token})
    return result["id"]


# ---------- 글 파일 ----------
def due_time(filename):
    """20261111-2200_장패드.txt -> 2026-11-11 22:00 (한국 시간)"""
    try:
        stamp = filename.split("_", 1)[0]
        return datetime.strptime(stamp, "%Y%m%d-%H%M").replace(tzinfo=KST)
    except ValueError:
        return None


def parse_file(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read().replace("\r\n", "\n")
    parts = []
    for chunk in raw.split("\n---\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        photos, topic = [], ""
        lines = chunk.split("\n")
        # 맨 위 "사진:" / "주제:" 줄은 글 내용이 아니라 설정 (순서 상관없음)
        while lines and lines[0].strip().replace(" :", ":").startswith(("사진:", "주제:")):
            key, value = lines.pop(0).split(":", 1)
            if key.strip() == "사진":
                photos = [n.strip() for n in value.split(",") if n.strip()]
            else:
                topic = value.strip().replace(".", "").replace("&", "")[:50]
        chunk = "\n".join(lines).strip()
        parts.append({"text": chunk, "photos": photos, "topic": topic})
    return parts


def check_parts(name, parts):
    problems = []
    if not parts:
        problems.append("글이 비어 있음")
    for i, p in enumerate(parts, 1):
        if "{쿠팡링크}" in p["text"]:
            problems.append(f"{i}번째 글에 쿠팡 링크가 아직 안 들어감")
        if len(p["text"]) > 500:
            problems.append(f"{i}번째 글이 {len(p['text'])}자 (500자까지)")
        if len(p["photos"]) > 20:
            problems.append(f"{i}번째 글의 사진이 {len(p['photos'])}장 (20장까지)")
        for photo in p["photos"]:
            if not os.path.exists(os.path.join(IMAGES, photo)):
                problems.append(f"images 폴더에 '{photo}' 사진이 없음")
    return problems


def queue_files():
    if not os.path.isdir(QUEUE):
        return []
    return sorted(f for f in os.listdir(QUEUE) if f.endswith(".txt"))


# ---------- 명령 ----------
def preview():
    now = datetime.now(KST)
    files = queue_files()
    if not files:
        print("posts/queue 폴더에 올릴 글이 없어요.")
        return
    for name in files:
        when = due_time(name)
        parts = parse_file(os.path.join(QUEUE, name))
        state = "시간 됨 (다음 실행 때 올라감)" if when and when <= now else "대기"
        print(f"■ {name}  |  {when.strftime('%m/%d %H:%M') if when else '파일 이름 오류'}  |  {state}")
        for problem in check_parts(name, parts):
            print(f"   ⚠️ {problem}")
        for i, p in enumerate(parts, 1):
            label = "본문" if i == 1 else "이어 쓰기"
            pics = f" + 사진 {len(p['photos'])}장" if p["photos"] else ""
            pics += f" · 주제 {p['topic']}" if p["topic"] else ""
            first_line = p["text"].split("\n")[0][:40]
            print(f"   {i}. {label}{pics}: {first_line}")
        print()


def run():
    now = datetime.now(KST)
    due = [f for f in queue_files() if (due_time(f) or now + timedelta(days=999)) <= now]
    if not due:
        print(f"{now:%m/%d %H:%M} 올릴 시간이 된 글이 없어요.")
        return

    token = read_token()
    base = image_base_url()
    me = call("GET", "/me", {"fields": "id,username", "access_token": token})
    os.makedirs(DONE, exist_ok=True)
    failed = False

    for name in due:
        path = os.path.join(QUEUE, name)
        parts = parse_file(path)
        problems = check_parts(name, parts)
        if any(p["photos"] for p in parts) and not base:
            problems.append("사진 주소를 만들 수 없음 (GitHub에서 실행해야 함)")
        if problems:
            print(f"✗ {name} 건너뜀: " + " / ".join(problems))
            failed = True
            continue
        try:
            previous, ids = None, []
            for p in parts:
                previous = publish(token, me["id"], p["text"], p["photos"], previous, base, p["topic"])
                ids.append(previous)
                time.sleep(5)
            shutil.move(path, os.path.join(DONE, name))
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(KST):%Y-%m-%d %H:%M}\t{name}\t{','.join(ids)}\n")
            print(f"✓ {name} 올림 ({len(ids)}개)")
        except RuntimeError as e:
            print(f"✗ {name} 실패: {e}")
            failed = True

    if failed:
        sys.exit(1)  # GitHub에서 실패 알림 메일이 오도록


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("미리보기", "preview"):
        preview()
    else:
        run()
