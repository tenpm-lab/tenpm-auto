import sys
import traceback, os, runpy
sys.path.insert(0, os.getcwd())
os.makedirs("bio", exist_ok=True)
try:
    runpy.run_path("make_site.py", run_name="__main__")
except Exception:
    open("bio/build_log.txt", "a", encoding="utf-8").write("\n[crash]\n" + traceback.format_exc())
