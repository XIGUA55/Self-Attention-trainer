import os
import ctypes
import time

# === Windows API ===
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

# 句柄常量
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11

# 控制台模式常量
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

# 窗口常量
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040

def disable_quick_edit_mode():
    """
    【核心修复】禁用快速编辑模式。
    防止用户点击窗口时进入"选择"状态导致程序挂起。
    """
    if os.name == 'nt':
        try:
            hIn = kernel32.GetStdHandle(STD_INPUT_HANDLE)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hIn, ctypes.byref(mode))
            
            # 移除 快速编辑模式 标志
            new_mode = mode.value & ~ENABLE_QUICK_EDIT_MODE
            # 必须加上 EXTENDED_FLAGS 才能生效
            new_mode = new_mode | ENABLE_EXTENDED_FLAGS
            
            kernel32.SetConsoleMode(hIn, new_mode)
        except:
            pass

def enable_vt_mode():
    """
    初始化：开启真彩色 + 禁用快速编辑
    """
    if os.name == 'nt':
        # 1. 禁用快速编辑 (防止挂起)
        disable_quick_edit_mode()
        
        # 2. 开启 VT 模式 (真彩色)
        try:
            hOut = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hOut, ctypes.byref(mode))
            mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(hOut, mode)
        except:
            pass

def get_best_hwnd():
    """
    获取最准确的窗口句柄。
    优先信任 GetForegroundWindow，因为之前测试证明它是对的。
    """
    # 获取当前进程ID
    my_pid = os.getpid()
    
    # 1. 尝试获取前台窗口
    hwnd_fg = user32.GetForegroundWindow()
    pid_fg = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd_fg, ctypes.byref(pid_fg))
    
    if pid_fg.value == my_pid:
        return hwnd_fg
    
    # 2. 如果前台不是我们，尝试 ConsoleWindow
    return kernel32.GetConsoleWindow()

def set_always_on_top(on=True):
    """强制置顶/取消置顶"""
    hwnd = kernel32.GetConsoleWindow()
    # -1 = 置顶, -2 = 取消置顶
    hwnd_topmost = -1 if on else -2
    # SWP_NOMOVE (0x2) | SWP_NOSIZE (0x1)
    user32.SetWindowPos(hwnd, hwnd_topmost, 0, 0, 0, 0, 0x0001 | 0x0002)

def force_focus():
    """
    强制把窗口拉到前台并置顶
    """
    hwnd = get_best_hwnd()
    if hwnd:
        # 还原
        user32.ShowWindow(hwnd, 9) # SW_RESTORE
        # 设为前台
        user32.SetForegroundWindow(hwnd)
        # 置顶
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

def resize_console(cols, lines):
    os.system(f'mode con: cols={cols} lines={lines}')
    
def clear_screen():
    os.system('cls')
def set_title(title):
    os.system(f'title {title}')