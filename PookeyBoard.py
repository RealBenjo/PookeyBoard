import tkinter as tk
import subprocess
import os
import json

# 1. PERMISSIONS & ENVIRONMENT
os.system("sudo chmod 0666 /dev/uinput > /dev/null 2>&1")
YDO_ENV = os.environ.copy()
YDO_ENV["YDOTOOL_SOCKET"] = "/tmp/ydotool.socket"

CONFIG_FILE = os.path.expanduser("~/.pookey.cfg")

class PookeyBoard:
    def __init__(self, root):
        self.root = root
        self.load_config()

        self.root.title("PookeyBoard")
        self.is_shift = False
        self.is_caps = False
        self.is_minimized = False
        self.old_height = self.cfg['height']
        self.mods = {"ctrl": False, "super": False, "alt": False, "altgr": False}
        self.mod_map = {"ctrl": "29", "super": "125", "alt": "56", "altgr": "100", "shift": "42", "shift_r": "54"}

        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        # Defaults to 960x360 based on the image proportions
        self.root.geometry(f"{self.cfg['width']}x{self.cfg['height']}")
        self.root.configure(bg="#111")

        self.update_key_map()
        self.setup_ui()

    def load_config(self):
        """Loads config with new icon support."""
        default_cfg = {
            "font_size": 14,
            "width": 960,
            "height": 360,
            "shift_icon": "⇧",
            "shift_r_icon": "⇧"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.cfg = {**default_cfg, **json.load(f)}
            except:
                self.cfg = default_cfg
        else:
            self.cfg = default_cfg
            self.save_config()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.cfg, f, indent=4)

    def update_key_map(self):
        # Dynamically map the icons from config to scancodes
        self.key_map = {
            "¸": "41", "1": "2", "2": "3", "3": "4", "4": "5", "5": "6", "6": "7", "7": "8", "8": "9", "9": "10", "0": "11", "'": "12", "+": "13", "back": "14",
            "tab": "15", "q": "16", "w": "17", "e": "18", "r": "19", "t": "20", "z": "21", "u": "22", "i": "23", "o": "24", "p": "25", "š": "26", "đ": "27", "enter": "28",
            "a": "30", "s": "31", "d": "32", "f": "33", "g": "34", "h": "35", "j": "36", "k": "37", "l": "38", "č": "39", "ć": "40", "ž": "43",
            "<": "86", "y": "44", "x": "45", "c": "46", "v": "47", "b": "48", "n": "49", "m": "50", ",": "51", ".": "52", "-": "53", "↑": "103",
            "space": "57", "←": "105", "↓": "108", "→": "106",
            self.cfg["shift_icon"]: "42",
            self.cfg["shift_r_icon"] + " ": "54"
        }

    def setup_ui(self):
        self.title_bar = tk.Frame(self.root, bg="#000", height=25)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)

        tk.Label(self.title_bar, text="PookeyBoard", fg="#666", bg="#000", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

        tk.Button(self.title_bar, text="✕", bg="#000", fg="#933", bd=0, command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        self.min_btn = tk.Button(self.title_bar, text="—", bg="#000", fg="#666", bd=0, command=self.toggle_minimize)
        self.min_btn.pack(side=tk.RIGHT, padx=5)

        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)

        self.main_frame = tk.Frame(self.root, bg="#111")
        self.main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Resize Grip (Bottom Right)
        self.grip = tk.Label(self.root, bg="#222", cursor="sizing")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", width=10, height=10)
        self.grip.bind("<B1-Motion>", self.on_resize)

        s_l = self.cfg["shift_icon"]
        s_r = self.cfg["shift_r_icon"]

        self.layout_normal = [
            ["¸","1","2","3","4","5","6","7","8","9","0","'","+","BACK"],
            ["TAB","q","w","e","r","t","z","u","i","o","p","š","đ","ENTER"],
            ["CAPS","a","s","d","f","g","h","j","k","l","č","ć","ž"],
            [s_l,"<","y","x","c","v","b","n","m",",",".","-","↑", s_r + " "],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","←","↓","→"]
        ]

        self.layout_shift = [
            ["¨","!","\"","#","$","%","&","/","(",")","=","?","*","BACK"],
            ["TAB","Q","W","E","R","T","Z","U","I","O","P","Š","Đ","ENTER"],
            ["CAPS","A","S","D","F","G","H","J","K","L","Č","Ć","Ž"],
            [s_l,">","Y","X","C","V","B","N","M",";",":","_","↑", s_r + " "],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","←","↓","→"]
        ]
        self.render_keys()

    def render_keys(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
        if self.is_minimized: return

        cur_layout = self.layout_shift if (self.is_shift or self.is_caps) else self.layout_normal
        key_font = ("Arial", self.cfg["font_size"], "bold")

        for row in cur_layout:
            row_frame = tk.Frame(self.main_frame, bg="#111")
            row_frame.pack(fill="both", expand=True)
            for key in row:
                bg = "#222"
                k_clean = key.strip()
                if k_clean == self.cfg["shift_icon"] and (self.is_shift or self.is_caps): bg = "#622"
                if k_clean.lower() in self.mods and self.mods[k_clean.lower()]: bg = "#252"

                btn = tk.Button(row_frame, text=key if k_clean.lower() != "space" else "",
                                fg="#ccc", bg=bg, font=key_font, relief="flat",
                                activebackground="#333", bd=0,
                                command=lambda k=key: self.handle_press(k))
                btn.pack(side=tk.LEFT, padx=1, pady=1, fill="both", expand=True)
                if k_clean.lower() == "space": btn.config(width=int(self.cfg['font_size'] * 0.8))

    def toggle_minimize(self):
        if not self.is_minimized:
            self.old_height = self.root.winfo_height()
            self.root.geometry(f"{self.root.winfo_width()}x25")
            self.min_btn.config(text="□")
            self.is_minimized = True
        else:
            self.root.geometry(f"{self.root.winfo_width()}x{self.old_height}")
            self.min_btn.config(text="—")
            self.is_minimized = False
        self.render_keys()

    def on_resize(self, event):
        # Enforce minimum size (960x360 as base reference)
        new_width = max(400, self.root.winfo_pointerx() - self.root.winfo_rootx())
        new_height = max(150, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{new_width}x{new_height}")
        self.cfg['width'], self.cfg['height'] = new_width, new_height
        self.save_config()

    def handle_press(self, key):
        k_val = key.strip()
        if k_val == self.cfg["shift_icon"]: self.is_shift = not self.is_shift
        elif k_val.lower() == "caps": self.is_caps = not self.is_caps
        elif k_val.lower() in self.mods:
            if k_val.lower() == "super": subprocess.run(["ydotool", "key", "125:1", "125:0"], env=YDO_ENV)
            else: self.mods[k_val.lower()] = not self.mods[k_val.lower()]
        else:
            self.send_hardware_signal(k_val.lower())
            if self.is_shift: self.is_shift = False
            for m in self.mods: self.mods[m] = False
        self.render_keys()

    def send_hardware_signal(self, key):
        lookup = {"¨": "41", "!": "2", "\"": "3", "#": "4", "$": "5", "%": "6", "&": "7", "/": "8", "(": "9", ")": "10", "=": "11", "?": "12", "*": "13", ">": "86", ";": "51", ":": "52", "_": "53"}
        code = lookup.get(key) or self.key_map.get(key)
        if code:
            cmd = ["ydotool", "key"]
            if self.is_shift or self.is_caps: cmd.append("42:1")
            for mod, active in self.mods.items():
                if active: cmd.append(f"{self.mod_map[mod]}:1")
            cmd.extend([f"{code}:1", f"{code}:0"])
            for mod, active in self.mods.items():
                if active: cmd.append(f"{self.mod_map[mod]}:0")
            if self.is_shift or self.is_caps: cmd.append("42:0")
            subprocess.run(cmd, env=YDO_ENV)

    def start_move(self, event): self.root.x, self.root.y = event.x, event.y
    def on_motion(self, event):
        x = self.root.winfo_x() + (event.x - self.root.x); y = self.root.winfo_y() + (event.y - self.root.y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk(); app = PookeyBoard(root); root.mainloop()
