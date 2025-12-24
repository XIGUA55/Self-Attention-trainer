import customtkinter as ctk
import tkinter as tk
import os

# 设置外观模式
ctk.set_appearance_mode("Dark")

class TerminalCore(ctk.CTk):
    """
    TUI 核心引擎：负责窗口绘制、光标保护、输入拦截、底层 I/O
    不包含任何游戏具体的业务逻辑。
    """
    def __init__(self, title="Terminal", width=1000, height=650):
        super().__init__()

        # === 1. 窗口设置 ===
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.attributes('-topmost', True)
        
        # 确定虚拟根目录 (用于显示 ~)
        self.system_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # === 2. UI 布局 ===
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.console = ctk.CTkTextbox(
            self,
            fg_color="#0c0c0c",       # 纯黑背景
            text_color="#cccccc",     # 灰白文字
            font=("Consolas", 14),
            corner_radius=0,
            activate_scrollbars=True
        )
        self.console.grid(row=0, column=0, sticky="nsew")
        
        # 获取底层对象
        self.tk_text = self.console._textbox 
        self._setup_tags()

        # === 3. 核心状态 ===
        self.input_locked = False
        self.command_history = []
        self.history_index = 0
        
        # === 4. 事件绑定 ===
        self.tk_text.bind("<Return>", self._on_enter)
        self.tk_text.bind("<BackSpace>", self._on_backspace)
        self.tk_text.bind("<Up>", self._on_up)
        self.tk_text.bind("<Down>", self._on_down)
        self.tk_text.bind("<Button-1>", self._on_click)
        self.tk_text.bind("<Key>", self._on_key_press)

    def _setup_tags(self):
        """配置颜色方案"""
        self.tk_text.tag_config("dir", foreground="#6699ff")
        self.tk_text.tag_config("exe", foreground="#00ff00")
        self.tk_text.tag_config("error", foreground="#ff5555")
        self.tk_text.tag_config("warn", foreground="#ffff55")
        self.tk_text.tag_config("system", foreground="#00ffff")
        self.tk_text.tag_config("dim", foreground="#666666")

    # ================= 公共 API (供 main.py 调用) =================

    def write(self, text, tag=None):
        """追加文本"""
        self.tk_text.insert("end", text, tag)
        self.tk_text.see("end")

    def clear_screen(self):
        """清屏"""
        self.tk_text.delete("1.0", "end")

    def new_prompt(self, custom_text=None):
        """生成提示符并锁定光标"""
        if custom_text:
             if not self.tk_text.get("end-2c") == "\n": self.write("\n")
             self.write(custom_text)
        else:
            cwd = os.getcwd()
            if cwd == self.system_root: path_str = "~"
            elif cwd.startswith(self.system_root): 
                path_str = f"~/{os.path.relpath(cwd, self.system_root)}".replace("\\", "/")
            else: path_str = cwd

            if not self.tk_text.get("end-2c") == "\n": self.write("\n")
            self.write(f"[root@node-01 {path_str}]# ")
        
        # 标记输入起点
        self.tk_text.mark_set("input_start", "insert")
        self.tk_text.mark_gravity("input_start", tk.LEFT)
        self.tk_text.see("end")
        self.input_locked = False

    def get_current_input(self):
        return self.tk_text.get("input_start", "end-1c")

    def clear_current_input(self):
        self.tk_text.delete("input_start", "end")
    
    def lock_input(self, locked=True):
        self.input_locked = locked

    # ================= 业务逻辑钩子 (需在 main.py 重写) =================

    def on_user_input(self, input_str):
        """当用户按下回车时调用此方法"""
        pass

    # ================= 底层事件处理 (通常不需要动) =================

    def _on_key_press(self, event):
        if self.input_locked: return "break"
        if (event.state & 0x0004) and event.keysym.lower() == 'c': return 
        if self.tk_text.compare("insert", "<", "input_start"):
            self.tk_text.mark_set("insert", "end")

    def _on_backspace(self, event):
        if self.input_locked: return "break"
        if self.tk_text.compare("insert", "<=", "input_start"): return "break"

    def _on_enter(self, event):
        if self.input_locked: return "break"
        
        user_input = self.get_current_input().strip()
        self.tk_text.mark_set("insert", "end")
        self.write("\n")
        
        # 历史记录逻辑
        if user_input:
            self.command_history.append(user_input)
            self.history_index = len(self.command_history)
        
        # 调用钩子，把控制权交给 main.py
        self.on_user_input(user_input)
        return "break"

    def _on_up(self, event):
        if self.input_locked: return "break"
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.clear_current_input()
            self.write(self.command_history[self.history_index])
        return "break"

    def _on_down(self, event):
        if self.input_locked: return "break"
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.clear_current_input()
            self.write(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.clear_current_input()
        return "break"

    def _on_click(self, event):
        self.tk_text.mark_set("insert", "end")
        self.tk_text.focus_set()
        return "break"