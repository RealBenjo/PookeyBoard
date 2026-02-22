import tkinter as tk
import subprocess
import os
import json
import urllib.request

# 1. PERMISSIONS & ENVIRONMENT
YDO_ENV = os.environ.copy()
YDO_ENV["YDOTOOL_SOCKET"] = "/tmp/ydotool.socket"

CONFIG_FILE = os.path.expanduser("~/.pookey.cfg")
DICT_FILE = os.path.expanduser("~/.pookey_words.json")
BASE_DICT_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2016/sl/sl_50k.txt"

class PookeyBoard:
    def __init__(self, root):
        self.root = root
        self.buffer = ""
        self.words = {}
        self.is_shift = False
        self.is_caps = False
        self.is_minimized = False
        self.repeat_job = None
        self.mods = {"ctrl": False, "alt": False, "altgr": False}
        self.mod_map = {"ctrl": "29", "alt": "56", "altgr": "100", "shift": "42"}

        self.load_config()
        self.old_height = self.cfg.get('height', 380)
        self.load_dictionary()

        self.scancodes = {
            "¸": "41", "1": "2", "2": "3", "3": "4", "4": "5", "5": "6", "6": "7", "7": "8", "8": "9", "9": "10", "0": "11", "'": "12", "+": "13",
            "¨": "41", "!": "2", "\"": "3", "#": "4", "$": "5", "%": "6", "&": "7", "/": "8", "(": "9", ")": "10", "=": "11", "?": "12", "*": "13",
            "~": "2", "ˇ": "3", "^": "4", "˘": "5", "°": "6", "˛": "7", "`": "8", "˙": "9", "´": "10", "˝": "11",
            "q": "16", "w": "17", "e": "18", "r": "19", "t": "20", "z": "21", "u": "22", "i": "23", "o": "24", "p": "25", "š": "26", "đ": "27",
            "\\": "16", "|": "86", "€": "18", "¶": "19", "ŧ": "20", "←": "21", "↓": "22", "→": "23", "ø": "24", "þ": "25", "÷": "26", "×": "27",
            "a": "30", "s": "31", "d": "32", "f": "33", "g": "34", "h": "35", "j": "36", "k": "37", "l": "38", "č": "39", "ć": "40", "ž": "43",
            "æ": "30", "„": "31", "“": "32", "[": "33", "]": "34", "ħ": "35", "ˀ": "36", "ł": "37", "ß": "40", "¤": "43",
            "<": "86", "y": "44", "x": "45", "c": "46", "v": "47", "b": "48", "n": "49", "m": "50", ",": "51", ".": "52", "-": "53",
            ">": "86", "‘": "44", "’": "45", "¢": "46", "@": "47", "{": "48", "}": "49", "§": "50", ";": "51", ":": "52", "_": "53", "—": "53",
            "back": "14", "tab": "15", "enter": "28", "space": "57", "super": "125",
            "↑": "103", "←_hw": "105", "↓_hw": "108", "→_hw": "106"
        }

        self.lay_n = [
            ["¸","1","2","3","4","5","6","7","8","9","0","'","+","BACK"],
            ["TAB","q","w","e","r","t","z","u","i","o","p","š","đ","ENTER"],
            ["CAPS","a","s","d","f","g","h","j","k","l","č","ć","ž"],
            ["⇧","<","y","x","c","v","b","n","m",",",".","-","↑", "⇧"],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","←","↓","→"]
        ]
        self.lay_s = [
            ["¨","!","\"","#","$","%","&","/","(",")","=","?","*","BACK"],
            ["TAB","Q","W","E","R","T","Z","U","I","O","P","Š","Đ","ENTER"],
            ["CAPS","A","S","D","F","G","H","J","K","L","Č","Ć","Ž"],
            ["⇧",">","Y","X","C","V","B","N","M",";",":","_","↑", "⇧"],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","←","↓","→"]
        ]
        self.lay_a = [
            ["¸","~","ˇ","^","˘","°","˛","`","˙","´","˝","¨","¸","BACK"],
            ["TAB","\\","|","€","¶","ŧ","←","↓","→","ø","þ","÷","×","ENTER"],
            ["CAPS","æ","„","“","[","]","ħ","ˀ","ł","ł","´","ß","¤"],
            ["⇧","|","‘","’","¢","@","{","}","§","<",">","—","↑", "⇧"],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","←","↓","→"]
        ]

        self.root.overrideredirect(True); self.root.attributes('-topmost', True)
        self.root.geometry(f"{self.cfg['width']}x{self.cfg['height']}+{self.cfg['x']}+{self.cfg['y']}")
        self.root.configure(bg="#111")
        self.setup_ui()

    def load_config(self):
        d = {"font_size": 14, "pred_font_size": 12, "width": 960, "height": 380, "x": 100, "y": 100}
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f: self.cfg = {**d, **json.load(f)}
            else: self.cfg = d
        except: self.cfg = d

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(self.cfg, f, indent=4)
        except: pass

    def load_dictionary(self):
        try:
            if os.path.exists(DICT_FILE):
                with open(DICT_FILE, 'r', encoding='utf-8') as f: self.words = json.load(f)
                keys = list(self.words.keys())
                for w in keys:
                    self.words[w] -= 1
                    if self.words[w] <= 0: del self.words[w]
                self.save_dictionary()
            else:
                self.words = {"pookey": 100}
        except: self.words = {"pookey": 100}

    def save_dictionary(self):
        try:
            with open(DICT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.words, f, ensure_ascii=False, indent=4)
        except: pass

    def setup_ui(self):
        tb = tk.Frame(self.root, bg="#000", height=25); tb.pack(fill="x"); tb.pack_propagate(False)
        tk.Label(tb, text="PookeyBoard", fg="#09f", bg="#000", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(tb, text="✕", bg="#000", fg="#933", bd=0, command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        self.min_btn = tk.Button(tb, text="—", bg="#000", fg="#666", bd=0, command=self.toggle_minimize); self.min_btn.pack(side=tk.RIGHT, padx=5)
        tb.bind("<Button-1>", self.start_move); tb.bind("<B1-Motion>", self.on_motion)

        self.pred_frame = tk.Frame(self.root, bg="#111", height=40); self.pred_frame.pack(fill="x", pady=(0, 2)); self.pred_frame.pack_propagate(False)
        self.pred_btns = []
        for i in range(3):
            # Middle button (index 1) is bold by default for best prediction
            b = tk.Button(self.pred_frame, text="", bg="#111", fg="#09f",
                          font=("Arial", self.cfg['pred_font_size'], "bold" if i==1 else "normal"),
                          relief="flat", bd=0, command=lambda idx=i: self.use_prediction(idx))
            b.pack(side=tk.LEFT, fill="both", expand=True, padx=1)
            self.pred_btns.append(b)

        self.main_frame = tk.Frame(self.root, bg="#111"); self.main_frame.pack(fill="both", expand=True, padx=1, pady=1)
        self.grip = tk.Label(self.root, bg="#222", cursor="sizing"); self.grip.place(relx=1.0, rely=1.0, anchor="se", width=10, height=10); self.grip.bind("<B1-Motion>", self.on_resize)
        self.render_keys()

    def render_keys(self):
        for w in self.main_frame.winfo_children(): w.destroy()
        if self.is_minimized: return
        layout = self.lay_a if self.mods["altgr"] else (self.lay_s if (self.is_shift or self.is_caps) else self.lay_n)
        for row in layout:
            rf = tk.Frame(self.main_frame, bg="#111"); rf.pack(fill="both", expand=True); rf.grid_rowconfigure(0, weight=1)
            for i, key in enumerate(row):
                kl = key.lower()
                if key in ["←","↓","→"] and row == layout[4]: kl = key + "_hw"
                w_val = 8 if kl=="space" else (1 if kl in ["←_hw","↓_hw","→_hw","↑"] else 2)
                rf.grid_columnconfigure(i, weight=w_val)
                bg = "#222"
                if kl == "⇧" and self.is_shift: bg = "#622"
                if kl == "caps" and self.is_caps: bg = "#622"
                if kl in self.mods and self.mods[kl]: bg = "#252"
                btn = tk.Button(rf, text=key if kl!="space" else "", fg="#ccc", bg=bg, font=("Arial", self.cfg["font_size"], "bold"), relief="flat", bd=0)
                btn.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
                btn.bind("<Button-1>", lambda e, k=key: self.on_key_down(k))
                btn.bind("<ButtonRelease-1>", lambda e: self.on_key_up())

    def on_key_down(self, key):
        self.handle_press(key)
        if key.lower() in ["back", "←", "↓", "→", "↑"]:
            self.repeat_job = self.root.after(500, lambda: self.repeat_step(key))

    def repeat_step(self, key):
        self.handle_press(key)
        self.repeat_job = self.root.after(50, lambda: self.repeat_step(key))

    def on_key_up(self):
        if self.repeat_job: self.root.after_cancel(self.repeat_job); self.repeat_job = None

    def handle_press(self, key):
        kl = key.lower()
        if kl == "⇧": self.is_shift = not self.is_shift; self.render_keys(); return
        if kl == "caps": self.is_caps = not self.is_caps; self.render_keys(); return
        if kl in self.mods: self.mods[kl] = not self.mods[kl]; self.render_keys(); return

        if kl == "back" and self.mods["ctrl"]:
            if self.buffer in self.words: del self.words[self.buffer]; self.save_dictionary()
            self.buffer = ""
        elif kl == "back": self.buffer = self.buffer[:-1]
        elif kl in ["space", "enter", "tab"]: self.buffer = ""
        elif len(key) == 1: self.buffer += kl

        if key in ["←","↓","→"] and not self.mods["altgr"]: kl = key + "_hw"
        self.send_hardware_signal(kl); self.update_predictions()
        if self.is_shift: self.is_shift = False; self.render_keys()

    def send_hardware_signal(self, kl):
        code = self.scancodes.get(kl)
        if self.mods["altgr"] and kl == "<": code = "51"
        elif self.mods["altgr"] and kl == ">": code = "52"
        if code:
            cmd = ["ydotool", "key"]
            if self.is_shift or self.is_caps: cmd.append("42:1")
            for m, a in self.mods.items():
                if a: cmd.append(f"{self.mod_map[m]}:1")
            cmd.extend([f"{code}:1", f"{code}:0"])
            for m, a in self.mods.items():
                if a: cmd.append(f"{self.mod_map[m]}:0")
            if self.is_shift or self.is_caps: cmd.append("42:0")
            subprocess.run(cmd, env=YDO_ENV)

    def update_predictions(self):
        if not self.buffer:
            for b in self.pred_btns: b.config(text="", bg="#111")
            return

        # Dictionary matches (highest score first, excluding exact buffer match)
        matches = sorted([w for w in self.words if w.startswith(self.buffer) and w != self.buffer], key=lambda w: self.words[w], reverse=True)

        # Slot 0 (LEFT): Buffer / New Word Entry
        is_new = self.buffer not in self.words
        self.pred_btns[0].config(text=self.buffer, bg="#004d66" if is_new else "#111", fg="#00d2ff" if is_new else "#09f")

        # Slot 1 (MIDDLE): Best prediction from dictionary
        self.pred_btns[1].config(text=matches[0] if len(matches) > 0 else "", bg="#1a1a1a")

        # Slot 2 (RIGHT): Second best prediction
        self.pred_btns[2].config(text=matches[1] if len(matches) > 1 else "", bg="#111")

    def use_prediction(self, idx):
        word = self.pred_btns[idx].cget("text")
        if not word: return
        self.words[word] = min(1000, self.words.get(word, 0) + 100); self.save_dictionary()
        cmd = ["ydotool", "key"] + ["14:1", "14:0"] * len(self.buffer)
        for char in word:
            c = self.scancodes.get(char.lower())
            if c: cmd.extend([f"{c}:1", f"{c}:0"])
        cmd.extend(["57:1", "57:0"]); subprocess.run(cmd, env=YDO_ENV)
        self.buffer = ""; self.update_predictions()

    def toggle_minimize(self):
        if not self.is_minimized: self.old_height = self.root.winfo_height(); self.root.geometry(f"{self.root.winfo_width()}x25"); self.is_minimized = True
        else: self.root.geometry(f"{self.root.winfo_width()}x{self.old_height}"); self.is_minimized = False
        self.render_keys()

    def on_resize(self, e):
        w, h = max(400, self.root.winfo_pointerx() - self.root.winfo_rootx()), max(150, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{w}x{h}"); self.cfg['width'], self.cfg['height'] = w, h; self.save_config()

    def start_move(self, e): self.root.x, self.root.y = e.x, e.y
    def on_motion(self, e):
        x, y = self.root.winfo_x() + (e.x - self.root.x), self.root.winfo_y() + (e.y - self.root.y)
        self.root.geometry(f"+{x}+{y}"); self.cfg['x'], self.cfg['y'] = x, y; self.save_config()

if __name__ == "__main__":
    root = tk.Tk(); app = PookeyBoard(root); root.mainloop()
