from playwright.sync_api import sync_playwright
import shutil, glob, os
W,H=1280,880
CUR='''
const c=document.createElement('div');c.id='fakecur';c.innerHTML='<svg width="34" height="34" viewBox="0 0 24 24"><path d="M4 2l15 9-6.5 1.6L9.5 19z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
Object.assign(c.style,{position:'fixed',left:'0',top:'0',zIndex:99999,pointerEvents:'none',transform:'translate(-4px,-2px)'});document.body.appendChild(c);
addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'},true);
addEventListener('mousedown',e=>{const r=document.createElement('div');Object.assign(r.style,{position:'fixed',left:(e.clientX-22)+'px',top:(e.clientY-22)+'px',width:'44px',height:'44px',borderRadius:'50%',border:'4px solid #fbbf24',zIndex:99998,pointerEvents:'none',transition:'all .45s ease-out',opacity:1});document.body.appendChild(r);requestAnimationFrame(()=>{r.style.transform='scale(1.8)';r.style.opacity=0});setTimeout(()=>r.remove(),600)},true);
'''
def svgpt(pg,x,y):
    return pg.evaluate("""([x,y])=>{const s=document.getElementById('scene');const p=s.createSVGPoint();p.x=x;p.y=y;const q=p.matrixTransform(s.getScreenCTM());return [q.x,q.y]}""",[x,y])
def person(pg,id):
    return pg.evaluate("id=>{const p=people[id];const s=document.getElementById('scene');const pt=s.createSVGPoint();pt.x=p.x;pt.y=p.y-30;const q=pt.matrixTransform(s.getScreenCTM());return [q.x,q.y]}",id)
def center(pg,sel):
    b=pg.locator(sel).first.bounding_box(); return [b['x']+b['width']/2,b['y']+b['height']/2]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome")
    ctx=b.new_context(viewport={"width":W,"height":H},record_video_dir="/tmp/off/vid",record_video_size={"width":W,"height":H})
    pg=ctx.new_page(); pg.goto("http://localhost:8765/index.html"); pg.wait_for_timeout(2500)
    pg.evaluate(CUR)
    pg.evaluate("window.scrollTo(0, document.getElementById('scene').getBoundingClientRect().top+scrollY-10)")
    pos=[640,700]; pg.mouse.move(*pos)
    def go(xy,steps=25,click=True,after=1300):
        pg.mouse.move(xy[0],xy[1],steps=steps); pg.wait_for_timeout(150)
        if click: pg.mouse.click(xy[0],xy[1])
        pg.wait_for_timeout(after)
    pg.wait_for_timeout(600)
    def goP(id,after=1600):
        for st in (14,6,3):
            xy=person(pg,id); pg.mouse.move(xy[0],xy[1],steps=st)
        xy=person(pg,id); pg.mouse.click(xy[0],xy[1]); pg.wait_for_timeout(after)
    goP("reply")
    go(center(pg,'[data-prop="snack"]'),after=2200)
    go(center(pg,'[data-prop="coffee"]'),after=1800)
    goP("gold")
    go(center(pg,'[data-prop="board"]'),after=2200)
    bb=pg.locator("#scene").bounding_box()
    ctx.close(); b.close()
    print(bb)
    v=glob.glob("/tmp/off/vid/*.webm")[0]; shutil.move(v,"/tmp/off/raw.webm")
