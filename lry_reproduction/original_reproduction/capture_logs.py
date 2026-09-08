"""Display saved, unmodified execution logs and take real window screenshots."""
import ctypes
from pathlib import Path
import tkinter as tk
from PIL import ImageGrab

ctypes.windll.user32.SetProcessDPIAware()
out = Path(__file__).resolve().parent
root = tk.Tk()
root.title("WBF original project reproduction - saved execution log")
root.geometry("1250x880+60+60")
root.attributes("-topmost", True)
label = tk.Label(root, font=("Consolas", 13), anchor="w")
label.pack(fill="x", padx=12, pady=8)
text = tk.Text(root, font=("Consolas", 11), wrap="word", padx=12, pady=12)
text.pack(fill="both", expand=True)
items = [("official_tests.log", "09_official_tests.png"),
         ("example.log", "10_example_output.png")]

def show(index=0):
    if index == len(items):
        root.destroy()
        return
    source, target = items[index]
    label.config(text="ORIGINAL PROJECT REPRODUCTION | Saved log: " + source)
    text.delete("1.0", "end")
    text.insert("1.0", (out / source).read_text(encoding="utf-8"))
    root.after(700, lambda: capture(index, target))

def capture(index, target):
    x, y = root.winfo_rootx(), root.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height())).save(out / target)
    show(index + 1)

root.after(300, show)
root.mainloop()
