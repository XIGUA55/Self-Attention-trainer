#!/bin/bash
# CyberFocus Auto-Scheduler v1.0
# This script reads kernel parameters (sysctl) and auto-tunes hyperparameters.

echo "[INFO] Reading system focus configuration..."
TARGET_TIME=$(sysctl -n kernel.focus_duration)

echo "[INFO] Target session time set to: ${TARGET_TIME} minutes"
echo "[INFO] Selecting optimal model architecture..."

# Execute training with auto-calculated epochs
python train.py --auto --target_time ${TARGET_TIME}
