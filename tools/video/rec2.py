from playwright.sync_api import sync_playwright
import shutil, glob
exec(open('/tmp/rec.py').read().split("with sync_playwright()")[0])  # CUR, svgpt, person, center
W,H=1280,880
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome")
    ctx=b.new_context(viewport={"width":W,"height":H},record_video_dir="/tmp/off/vid2",record_video_size={"width":W,"height":H})
    pg=ctx.new_page(); pg.goto("http://localhost:8765/index.html"); pg.wait_for_timeout(2500)
    pg.evaluate(CUR)
    pg.evaluate("window.scrollTo(0, document.getElementById('scene').getBoundingClientRect().top+scrollY-10)")
    pg.mouse.move(640,700); pg.wait_for_timeout(1200)
    def goP(id,after=1500):
        for st in (14,6,3):
            xy=person(pg,id); pg.mouse.move(xy[0],xy[1],steps=st)
        xy=person(pg,id); pg.mouse.click(xy[0],xy[1]); pg.wait_for_timeout(after)
    goP("editor",1600)
    pg.click('#px') if pg.locator('#px').is_visible() else None
    c=center(pg,'#clock'); pg.mouse.move(c[0],c[1],steps=20); pg.wait_for_timeout(150); pg.mouse.click(c[0],c[1]); pg.wait_for_timeout(4200)
    goP("gold",1800)
    ctx.close(); b.close()
    v=glob.glob("/tmp/off/vid2/*.webm")[0]; shutil.move(v,"/tmp/off/raw2.webm")
