import tkinter as tk
import subprocess
import os

# Permissions & Engine Prep
os.system("sudo chmod 0666 /dev/uinput > /dev/null 2>&1")

YDO_ENV = os.environ.copy()
YDO_ENV["YDOTOOL_SOCKET"] = "/tmp/ydotool.socket"

class PookeyBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("PookeyBoard")
        self.is_shift = False
        self.is_caps = False

        # Modifier States
        self.mods = {"CTRL": False, "SUPER": False, "ALT": False, "ALTGR": False}
        self.mod_map = {"CTRL": "29", "SUPER": "125", "ALT": "56", "ALTGR": "100"}

        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.setup_ui()

    def setup_ui(self):
        # Title Bar
        self.title_bar = tk.Frame(self.root, bg="#111", relief="raised", bd=1)
        self.title_bar.pack(fill="x")
        self.title_label = tk.Label(self.title_bar, text=" ⌨️ Pookey Slovenian QWERTZ", fg="#888", bg="#111", font=("Arial", 9, "bold"))
        self.title_label.pack(side=tk.LEFT)
        tk.Button(self.title_bar, text=" [X] ", bg="#111", fg="#f44", bd=0, command=self.root.destroy, takefocus=0).pack(side=tk.RIGHT)

        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)

        self.key_frame = tk.Frame(self.root, bg="#222", bd=2, relief="groove")
        self.key_frame.pack(fill="both", expand=True)

        # SLOVENIAN QWERTZ LAYOUT
        self.layout_normal = [
            ["¸","1","2","3","4","5","6","7","8","9","0","'","+","BACK"],
            ["TAB","q","w","e","r","t","z","u","i","o","p","š","đ","ENTER"],
            ["CAPS","a","s","d","f","g","h","j","k","l","č","ć","ž"],
            ["SHIFT","<","y","x","c","v","b","n","m",",",".","-","UP"],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","LEFT","DOWN","RIGHT"]
        ]

        self.layout_shift = [
            ["¨","!","\"","#","$","%","&","/","(",")","=","?","*","BACK"],
            ["TAB","Q","W","E","R","T","Z","U","I","O","P","Š","Đ","ENTER"],
            ["CAPS","A","S","D","F","G","H","J","K","L","Č","Ć","Ž"],
            ["SHIFT",">","Y","X","C","V","B","N","M",";",":","_","UP"],
            ["CTRL","SUPER","ALT","SPACE","ALTGR","LEFT","DOWN","RIGHT"]
        ]
        self.render_keys()

    def render_keys(self):
        for widget in self.key_frame.winfo_children():
            widget.destroy()

        active_shift = self.is_shift or self.is_caps
        current_layout = self.layout_shift if active_shift else self.layout_normal

        for row in current_layout:
            row_frame = tk.Frame(self.key_frame, bg="#222")
            row_frame.pack(fill="both", expand=True)
            for key in row:
                bg_color = "#444"
                if key == "SHIFT" and self.is_shift: bg_color = "#933" # Dark Red
                if key == "CAPS" and self.is_caps: bg_color = "#933"
                if key in self.mods and self.mods[key]: bg_color = "#373" # Dark Green

                w = 8 if key in ["SPACE", "ENTER", "BACK", "SHIFT"] else 4
                btn = tk.Button(row_frame, text=key, width=w, height=2, fg="white", bg=bg_color,
                                activebackground="#666", takefocus=0, command=lambda k=key: self.handle_press(k))
                btn.pack(side=tk.LEFT, padx=1, pady=1, fill="both", expand=True)

    def handle_press(self, key):
        if key == "SHIFT":
            self.is_shift = not self.is_shift
            self.render_keys()
        elif key == "CAPS":
            self.is_caps = not self.is_caps
            self.render_keys()
        elif key in self.mods:
            if key == "SUPER":
                # Instant fire for Super key
                subprocess.run(["ydotool", "key", "125:1", "125:0"], env=YDO_ENV)
            else:
                self.mods[key] = not self.mods[key]
            self.render_keys()
        else:
            self.type_key(key)
            # Auto-reset Shift after one key
            if self.is_shift:
                self.is_shift = False
            # Auto-reset Mods after one key (CTRL+C, etc)
            for m in self.mods: self.mods[m] = False
            self.render_keys()

    def type_key(self, key):
        # 1. Action Keys (Must use scancodes)
        special = {
            "BACK": "14", "ENTER": "28", "TAB": "15", "SPACE": "57",
            "UP": "103", "DOWN": "108", "LEFT": "105", "RIGHT": "106",
            "¸": "41", "'": "12", "+": "13", "<": "86", "-": "53"
        }

        try:
            # 2. Handle AltGr + v override for @
            if self.mods["ALTGR"] and key.lower() == "v":
                subprocess.run(["ydotool", "type", "@"], env=YDO_ENV)
                return

            # 3. Handle Special Keys (Arrows, Tab, etc)
            if key in special:
                cmd = ["ydotool", "key"]
                # Add modifiers if any are active
                for mod, active in self.mods.items():
                    if active: cmd.append(f"{self.mod_map[mod]}:1")

                cmd.extend([f"{special[key]}:1", f"{special[key]}:0"])

                for mod, active in self.mods.items():
                    if active: cmd.append(f"{self.mod_map[mod]}:0")
                subprocess.run(cmd, env=YDO_ENV)

            # 4. Handle Normal Typing (š, đ, z, y, etc)
            else:
                if any(self.mods.values()):
                    # If CTRL or ALT is active, we try to wrap the character
                    # This works for combos like CTRL+c
                    cmd = ["ydotool", "key"]
                    for mod, active in self.mods.items():
                        if active: cmd.append(f"{self.mod_map[mod]}:1")
                    subprocess.run(cmd, env=YDO_ENV) # Hold mods
                    subprocess.run(["ydotool", "type", key], env=YDO_ENV) # Type char
                    # Release mods
                    cmd = ["ydotool", "key"]
                    for mod, active in self.mods.items():
                        if active: cmd.append(f"{self.mod_map[mod]}:0")
                    subprocess.run(cmd, env=YDO_ENV)
                else:
                    # Just standard typing
                    subprocess.run(["ydotool", "type", key], env=YDO_ENV)

        except Exception as e:
            print(f"Error: {e}")

    def start_move(self, event): self.root.x, self.root.y = event.x, event.y
    def on_motion(self, event):
        deltax = event.x - self.root.x
        deltay = event.y - self.root.y
        self.root.geometry(f"+{self.root.winfo_x() + deltax}+{self.root.winfo_y() + deltay}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PookeyBoard(root)
    root.mainloop()
