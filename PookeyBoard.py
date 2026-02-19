import tkinter as tk
import subprocess
import os

# 1. PERMISSIONS & ENVIRONMENT
os.system("sudo chmod 0666 /dev/uinput > /dev/null 2>&1")
YDO_ENV = os.environ.copy()
YDO_ENV["YDOTOOL_SOCKET"] = "/tmp/ydotool.socket"

class PookeyBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("PookeyBoard")
        self.is_shift = False
        self.is_caps = False
        self.mods = {"ctrl": False, "super": False, "alt": False, "altgr": False}
        self.mod_map = {"ctrl": "29", "super": "125", "alt": "56", "altgr": "100", "shift": "42", "shift_r": "54"}

        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.geometry("850x300") # Slightly taller to accommodate bigger text
        self.root.configure(bg="#111")

        # Hardware Mapping
        self.key_map = {
            "¸": "41", "1": "2", "2": "3", "3": "4", "4": "5", "5": "6", "6": "7", "7": "8", "8": "9", "9": "10", "0": "11", "'": "12", "+": "13", "back": "14",
            "tab": "15", "q": "16", "w": "17", "e": "18", "r": "19", "t": "20", "z": "21", "u": "22", "i": "23", "o": "24", "p": "25", "š": "26", "đ": "27", "enter": "28",
            "a": "30", "s": "31", "d": "32", "f": "33", "g": "34", "h": "35", "j": "36", "k": "37", "l": "38", "č": "39", "ć": "40", "ž": "43",
            "<": "86", "y": "44", "x": "45", "c": "46", "v": "47", "b": "48", "n": "49", "m": "50", ",": "51", ".": "52", "-": "53", "up": "103",
            "space": "57", "left": "105", "down": "108", "right": "106", "shift_r": "54"
        }

        self.setup_ui()

    def setup_ui(self):
        self.title_bar = tk.Frame(self.root, bg="#000", height=22)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        tk.Label(self.title_bar, text=" 🇸🇮 Pookey 4.2", fg="#666", bg="#000", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        tk.Button(self.title_bar, text="✕", bg="#000", fg="#933", bd=0, command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)

        self.key_frame = tk.Frame(self.root, bg="#111")
        self.key_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.layout_normal = [
            ["¸","1","2","3","4","5","6","7","8","9","0","'","+","BACK"],
            ["TAB","q","w","e","r","t","z","u","i","o","p","š","đ","ENTER"],
            ["CAPS","a","s","d","f","g","h","j","k","l","č","ć","ž"],
            ["SHIFT","<","y","x","c","v","b","n","m",",",".","-","UP","SHIFT "],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","LEFT","DOWN","RIGHT"]
        ]
        
        self.layout_shift = [
            ["¨","!","\"","#","$","%","&","/","(",")","=","?","*","BACK"],
            ["TAB","Q","W","E","R","T","Z","U","I","O","P","Š","Đ","ENTER"],
            ["CAPS","A","S","D","F","G","H","J","K","L","Č","Ć","Ž"],
            ["SHIFT",">","Y","X","C","V","B","N","M",";",":","_","UP","SHIFT "],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","LEFT","DOWN","RIGHT"]
        ]
        self.render_keys()

    def render_keys(self):
        for widget in self.key_frame.winfo_children(): widget.destroy()
        cur_layout = self.layout_shift if (self.is_shift or self.is_caps) else self.layout_normal
        
        # KEY FONT - UPDATED TO 12 BOLD
        key_font = ("Arial", 12, "bold")

        for row in cur_layout:
            row_frame = tk.Frame(self.key_frame, bg="#111")
            row_frame.pack(fill="both", expand=True)
            for key in row:
                bg = "#222"
                is_active_shift = (key.strip() == "SHIFT") and (self.is_shift or self.is_caps)
                if is_active_shift: bg = "#622"
                if key.lower() in self.mods and self.mods[key.lower()]: bg = "#252"
                
                k_clean = key.strip().lower()
                
                if k_clean == "space":
                    btn = tk.Button(row_frame, text="", fg="#ccc", bg=bg, font=key_font,
                                    relief="flat", activebackground="#333", bd=0, width=30,
                                    command=lambda k="space": self.handle_press(k))
                else:
                    btn = tk.Button(row_frame, text=key, fg="#ccc", bg=bg, font=key_font,
                                    relief="flat", activebackground="#333", bd=0,
                                    command=lambda k=key: self.handle_press(k))
                
                btn.pack(side=tk.LEFT, padx=1, pady=1, fill="both", expand=True)

    def handle_press(self, key):
        k_low = key.strip().lower()
        if k_low == "shift":
            self.is_shift = not self.is_shift
        elif k_low == "caps":
            self.is_caps = not self.is_caps
        elif k_low in self.mods:
            if k_low == "super": subprocess.run(["ydotool", "key", "125:1", "125:0"], env=YDO_ENV)
            else: self.mods[k_low] = not self.mods[k_low]
        else:
            self.send_hardware_signal(k_low)
            if self.is_shift: self.is_shift = False
            for m in self.mods: self.mods[m] = False
        self.render_keys()

    def send_hardware_signal(self, key):
        lookup = {
            "¨": "41", "!": "2", "\"": "3", "#": "4", "$": "5", "%": "6", "&": "7", "/": "8", "(": "9", ")": "10", "=": "11", "?": "12", "*": "13",
            ">": "86", ";": "51", ":": "52", "_": "53"
        }
        key_code_name = "shift_r" if key == "shift " else key
        code = lookup.get(key) or self.key_map.get(key_code_name)
        
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