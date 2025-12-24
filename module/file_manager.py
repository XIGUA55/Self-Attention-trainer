import os
from module.config import WORKSPACE_DIR, TASKS_DATA

def init_workspace():
    """初始化虚拟文件系统"""
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
        
    # 1. 生成 Python 训练脚本
    models = TASKS_DATA.get("models", [])
    for m in models:
        safe_name = m['name'].replace("-", "_").replace(" ", "_").lower()
        filename = f"train_{safe_name}.py"
        filepath = os.path.join(WORKSPACE_DIR, filename)
        
        content = f"""# PyTorch Training Script for {m['name']}
# Architecture: Transformer / CNN
# Base Ops: {m['base_ops']}

import torch
from cyber_focus import Trainer

def main():
    print("Initializing distributed backend...")
    model = Trainer(model_name="{m['name']}")
    model.fit()

if __name__ == "__main__":
    main()
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    # 2. 【新增】生成自动训练脚本 (.sh)
    sh_path = os.path.join(WORKSPACE_DIR, "auto_scheduler.sh")
    sh_content = """#!/bin/bash
# CyberFocus Auto-Scheduler v1.0
# This script reads kernel parameters (sysctl) and auto-tunes hyperparameters.

echo "[INFO] Reading system focus configuration..."
TARGET_TIME=$(sysctl -n kernel.focus_duration)

echo "[INFO] Target session time set to: ${TARGET_TIME} minutes"
echo "[INFO] Selecting optimal model architecture..."

# Execute training with auto-calculated epochs
python train.py --auto --target_time ${TARGET_TIME}
"""
    with open(sh_path, 'w', encoding='utf-8') as f:
        f.write(sh_content)

    return len(models) + 1