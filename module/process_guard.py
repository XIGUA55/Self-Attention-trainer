import time
import ctypes
import psutil
import os
from .config import BLACKLIST_PROCESSES, WHITELIST_SYSTEM

# 加载 user32.dll
if os.name == 'nt':
    user32 = ctypes.windll.user32
else:
    user32 = None

def get_active_process_name():
    """获取当前前台窗口的进程名"""
    if not user32: return None
    
    try:
        # 1. 获取前台窗口句柄
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0: return None
        
        # 2. 获取进程ID (PID)
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # 3. 通过 PID 获取进程名
        # [优化] 增加异常处理，防止进程瞬间消失导致报错
        try:
            process = psutil.Process(pid.value)
            return process.name().lower()
        except psutil.NoSuchProcess:
            return None
        except psutil.AccessDenied:
            return None # 无法访问系统级进程通常意味着它是安全的系统进程
    except:
        return None

def check_violation():
    """
    检查是否违规
    返回: (是否违规, 违规进程名)
    """
    active_name = get_active_process_name()
    
    if not active_name:
        return False, None
        
    # [新增] 自身进程白名单
    # 获取当前运行脚本的 PID，防止自己把自己当成违规进程
    try:
        current_pid = os.getpid()
        # 如果前台进程就是我自己，直接放行
        # 注意：这里需要再次获取 active_process 的 pid 进行对比，或者简单地信任 python.exe
        # 简单方案：如果 active_name 是 python.exe 且我们在运行，通常是安全的
        if active_name == "python.exe": 
            return False, None
    except:
        pass

    # 如果是系统白名单，直接放行
    if active_name in WHITELIST_SYSTEM:
        return False, None
        
    # 检查黑名单
    if active_name in BLACKLIST_PROCESSES:
        return True, active_name
        
    return False, None