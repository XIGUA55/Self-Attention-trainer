

import json
import os
from .config import SAVE_FILE

def load_game_data():
    """
    加载存档。如果文件不存在或损坏，返回默认初始数据。
    """
    # 1. 定义初始默认状态
    default_data = {
        "coins": 0,
        "gpu_level": 0,
        "total_hours": 0.0,
        "focus_duration": 25, # 默认专注时间
        "strict_mode": False,  # 严格模式状态
        "level": 0,           # [新增] 当前等级
        "Exp": 0              # [新增] 当前经验值
    }
    
    final_data = default_data.copy()

    # 2. 尝试读取
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
                # 3. 增量更新：只更新存档里有的字段，保留默认值里新增的字段
                for key, value in loaded_data.items():
                    final_data[key] = value
                    
        except Exception as e:
            print(f"[System Error] Corrupted save file. Creating new one. (Reason: {e})")
            pass
            
    return final_data

def save_game_data(data):
    """
    保存存档。会自动创建父目录。
    """
    try:
        dir_path = os.path.dirname(SAVE_FILE)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to save game data!")
        print(f"Target path: {SAVE_FILE}")
        print(f"Error detail: {e}\n")