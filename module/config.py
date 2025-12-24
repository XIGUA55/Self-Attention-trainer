import os
import json

# ================= 路径修正逻辑 =================
# 1. 获取 config.py 所在的目录 (即: .../你的项目/module)
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 获取 MODULE_DIR 的父目录 (即: .../你的项目/ [根目录])
# 这就是我们要的真正的 Base Directory
BASE_DIR = os.path.dirname(MODULE_DIR)

# ================= 下面的路径拼接保持不变 =================
# 现在这些路径会自动拼接到根目录下
SAVE_FILE = os.path.join(BASE_DIR, "./save/cyber_save.json")
HARDWARE_FILE = os.path.join(BASE_DIR, "./data/hardware.json")
TASKS_FILE = os.path.join(BASE_DIR, "./data/tasks.json")
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")

# ================= 游戏平衡参数 (修复点) =================
# 目标挂机时间 (秒) -> 40分钟
TARGET_SESSION_TIME = 40 * 60 
# 收益系数 (每 1 TFLOPs 运算量的收益)
REWARD_FACTOR = 0.05           
# =======================================================

DEBUG_MODE = False

# 窗口尺寸 (字符数)
MINI_COLS = 60
MINI_LINES = 5
SHELL_COLS = 100
SHELL_LINES = 30

def load_json_config(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_val
    return default_val

# 保底数据
DEFAULT_HARDWARE = [{"name": "CPU-Fallback", "tflops": 0.1, "cost": 0}]
DEFAULT_TASKS = {"models": [], "datasets": []}

# 加载数据
HARDWARE = load_json_config(HARDWARE_FILE, DEFAULT_HARDWARE)
TASKS_DATA = load_json_config(TASKS_FILE, DEFAULT_TASKS)
DEFAULT_STRICT_MODE = False 

# 进程黑名单 (小写，包含后缀)
# 当这些程序处于前台时，训练会立即崩溃
BLACKLIST_PROCESSES = [
    "msedge.exe", 
    "firefox.exe",
    "steam.exe",
    "wechat.exe",
    "qq.exe",
    "discord.exe",
    "douyin.exe",
    "dingtalk.exe" # 甚至可以是钉钉
]

# 允许的例外 (白名单)
# 比如你正在查资料，允许 edge 存在，但必须手动把 edge 从黑名单移除
# 这里存放必须要有的系统进程，防止误杀自己
WHITELIST_SYSTEM = [
    "python.exe",
    "cmd.exe",
    "conhost.exe",
    "windowsterminal.exe",
    "code.exe",  # VS Code (写代码允许)
    "explorer.exe" # 资源管理器
]