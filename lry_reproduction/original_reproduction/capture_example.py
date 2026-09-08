"""Run the unchanged upstream example; capture its windows and press Space."""
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time
from ctypes import wintypes
from PIL import ImageGrab

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
user32.FindWindowW.restype = wintypes.HWND
names = ["wbf_two_models_before", "wbf_two_models_after",
         "wbf_one_model_before", "wbf_one_model_after",
         "nms_before", "nms_after", "soft_nms_before", "soft_nms_after"]
results = []
with (OUT / "example.log").open("w", encoding="utf-8") as log:
    log.write("Command: python examples/example.py\n")
    log.flush()
    process = subprocess.Popen([sys.executable, "-u", "examples/example.py"],
                               cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    time.sleep(1)
    children = subprocess.check_output([
        "powershell", "-NoProfile", "-Command",
        f"Get-CimInstance Win32_Process -Filter 'ParentProcessId={process.pid}' | Select-Object -ExpandProperty ProcessId"
    ], text=True)
    allowed_pids = {process.pid, *(int(p) for p in children.split())}
    deadline = time.monotonic() + 120
    while process.poll() is None and time.monotonic() < deadline:
        hwnd = user32.FindWindowW(None, "image")
        pid = wintypes.DWORD()
        if hwnd:
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if hwnd and pid.value in allowed_pids:
            time.sleep(0.5)
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            index = len(results)
            name = names[index] if index < len(names) else f"extra_{index}"
            filename = f"{index + 1:02d}_{name}.png"
            ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(OUT / filename)
            results.append(filename)
            user32.PostMessageW(hwnd, 0x0100, 0x20, 0)
            user32.PostMessageW(hwnd, 0x0101, 0x20, 0)
            time.sleep(0.7)
        else:
            time.sleep(0.1)
    if process.poll() is None:
        process.terminate()
        process.wait()
        log.write("Timed out after 120 seconds.\n")
    log.write(f"\nExit code: {process.returncode}\n")
(OUT / "example_capture.json").write_text(json.dumps(
    {"exit_code": process.returncode, "screenshots": results}, indent=2), encoding="utf-8")
print(json.dumps({"exit_code": process.returncode, "screenshots": results}, indent=2))
sys.exit(process.returncode)
