import time
import math
import random
import json
import os
import threading

from .config import HARDWARE
from .storage import save_game_data
from . import process_guard 

TIME_CONSTANT = 0.05

def load_tasks():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'tasks.json')
    if not os.path.exists(path):
        return {"models": [{"name": "Fallback-Model", "base_ops": 100, "difficulty": 1}]}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_menu_data(game_data):
    """
    返回给 main.py 用于显示选单的数据
    """
    tasks_data = load_tasks()
    gpu_idx = min(game_data.get('gpu_level', 0), len(HARDWARE)-1)
    gpu = HARDWARE[gpu_idx]
    tflops = max(0.1, gpu['tflops'])
    target_focus_time = game_data.get('focus_duration', 25)
    player_level = game_data.get('level', 1)
    
    menu_lines = []
    menu_lines.append(f"usage: train.py --device {gpu['name']}")
    menu_lines.append(f"CURRENT HARDWARE: {gpu['tflops']} TFLOPS | Player Lv.{player_level}")
    menu_lines.append(f"STANDARD MODEL LIBRARY:")
    menu_lines.append(f"  {'ID':<4} {'Model Name':<20} {'Diff':<6} {'Est.Speed':<12} {'Rec.Epochs'}")

    options = {}
    for idx, model in enumerate(tasks_data['models'], 1):
        mins_per_epoch = (model['base_ops'] / tflops) * TIME_CONSTANT
        auto_epochs = int(target_focus_time / mins_per_epoch)
        if auto_epochs < 1: auto_epochs = 1
        
        if mins_per_epoch < 1.0: time_str = f"{mins_per_epoch*60:.1f}s/ep"
        else: time_str = f"{mins_per_epoch:.2f}m/ep"
        
        menu_lines.append(f"  {idx:<4} {model['name']:<20} {model.get('difficulty', 1):<6} {time_str:<12} {auto_epochs}")
        
        options[str(idx)] = {
            "model": model,
            "mins_per_epoch": mins_per_epoch,
            "auto_epochs": auto_epochs
        }
    return menu_lines, options

def start_training_session(game_data, selected_option, user_epochs, user_lr, ui_callbacks):
    model = selected_option['model']
    mins_per_epoch = selected_option['mins_per_epoch']
    
    # 默认参数处理
    epochs = int(user_epochs) if user_epochs else selected_option['auto_epochs']
    
    # 如果用户没填 LR，默认 0.001
    learning_rate = float(user_lr) if user_lr else 0.001 

    threading.Thread(target=_run_training_loop, 
                     args=(game_data, model, epochs, learning_rate, mins_per_epoch, ui_callbacks), 
                     daemon=True).start()

def _run_training_loop(game_data, model, epochs, learning_rate, mins_per_epoch, ui):
    ui['set_mini_mode'](True)
    time.sleep(0.5)

    gpu_idx = game_data.get('gpu_level', 0)
    gpu_name = HARDWARE[min(gpu_idx, len(HARDWARE)-1)]['name']
    
    # --- 0. 识别任务类型 ---
    mission_reqs = model.get('__mission_reqs') 
    mission_rewards = model.get('__rewards')
    is_mission = (mission_reqs is not None)

    # --- 1. 初始化显示 ---
    ui['print'](f"\n[INIT] CUDA context: {gpu_name}")
    if is_mission:
        ui['print'](f"[CONTRACT] Client Protocol Initiated.", "warn")
        if mission_reqs.get('target_acc'):
            ui['print'](f"[TARGET] Required Accuracy: >{mission_reqs['target_acc']}%")
        else:
            ui['print'](f"[TARGET] Stability Run: Complete {epochs} epochs")
    else:
        ui['print'](f"[CONF] Model: {model['name']} | LR: {learning_rate}")

    ui['print']("-" * 65)
    
    # --- 2. 物理引擎参数 (Physics) ---
    base_loss = model.get('max_loss', 2.5)
    target_loss = 0.05 
    
    instability = learning_rate * 1000.0 
    potential_factor = 1.0 - math.exp(-learning_rate * 500) 
    
    steps_per_epoch = 100 
    base_step_delay = (mins_per_epoch * 60) / steps_per_epoch
    if base_step_delay < 0.01: base_step_delay = 0.01

    current_loss = base_loss
    focus_violation_count = 0

    # [新增] 平滑参数，模仿tqdm
    smoothing = 0.3
    avg_speed = None 

    try:
        # ==================== MAIN LOOP ====================
        for current_epoch in range(1, epochs + 1):
            ui['print'](f"Epoch {current_epoch}/{epochs}")
            
            epoch_start = time.time()
            
            for step in range(steps_per_epoch):
                # 严格模式检测
                if game_data.get('strict_mode', False) and step % 15 == 0:
                    violation, _ = process_guard.check_violation()
                    if violation: focus_violation_count += 1

                # 模拟 Loss 曲线
                total_progress = ((current_epoch - 1) * steps_per_epoch + step) / (epochs * steps_per_epoch)
                decay = math.exp(-4.0 * total_progress) 
                ideal_val = target_loss + (base_loss - target_loss) * decay
                
                noise_scale = instability * 0.05 * (decay + 0.1) 
                noise = random.uniform(-noise_scale, noise_scale)
                if random.random() < (learning_rate * 10): 
                    noise += random.uniform(0.1, 0.5)
                
                display_loss = max(0.0001, ideal_val + noise)
                current_loss = display_loss 
                
                # --- [修正核心] 速度计算逻辑 ---
                # 1. 计算当前Step预计耗时 (模拟真实运算时间)
                step_sleep = base_step_delay * random.uniform(0.9, 1.1)
                
                # 2. 计算瞬时速度 (iteration per second)
                # 避免除以0
                curr_rate = 1.0 / step_sleep if step_sleep > 0 else 0.0
                
                # 3. 使用指数移动平均 (EMA) 平滑速度，防止数字跳动
                if avg_speed is None:
                    avg_speed = curr_rate
                else:
                    avg_speed = (1 - smoothing) * avg_speed + smoothing * curr_rate
                
                # 4. 基于平滑后的速度计算剩余时间 (ETA)
                steps_left = (steps_per_epoch - (step + 1))
                eta = steps_left / avg_speed if avg_speed > 0 else 0

                remaining_sleep = step_sleep
                
                # 在单个 step 等待期间刷新 UI
                # 这里的循环只负责"走时间"，不应该重新计算速度，否则会导致速度在等待期间不断下降
                while remaining_sleep > 0:
                    chunk = min(0.1, remaining_sleep) # 刷新频率 10Hz
                    time.sleep(chunk)
                    remaining_sleep -= chunk
                    
                    # 实时更新经过的时间
                    elapsed = time.time() - epoch_start
                    current_step_count = step + 1
                    
                    # 构造 TQDM 风格字符串
                    percent = int(current_step_count / steps_per_epoch * 100)
                    bar_str = _make_progress_bar(percent, length=20)
                    
                    # 格式: 100%|██████████| 50/50 [00:02<00:00, 24.32it/s, loss=0.0123]
                    # 注意：这里直接使用上面计算好的 avg_speed 和 eta，不在循环内变动
                    info_str = f"{percent:>3}%|{bar_str}| {current_step_count}/{steps_per_epoch} [{_fmt(elapsed)}<{_fmt(eta)}, {avg_speed:.2f}it/s, loss={display_loss:.4f}]"
                    
                    ui['update_bar'](info_str)

    except Exception as e:
        ui['print'](f"[ERR] Training interrupted: {e}", "error")
        time.sleep(2)
        ui['set_mini_mode'](False)
        ui['finished'](error_result) # <--- 加上参数
        return

    # ================= 3. 验证与结算 (Validation Phase) =================
    
    ui['print']("\n" + "="*65)
    ui['print']("VALIDATING MODEL PERFORMANCE...")
    time.sleep(1.0)
    
    # --- 计算基础 Accuracy ---
    hw_level = HARDWARE[min(gpu_idx, len(HARDWARE)-1)].get('level', 1)
    
    base_score = 50.0 + (hw_level * 2) 
    potential_score = 40.0 * potential_factor 
    
    risk_penalty = 0
    crash_chance = max(0, (learning_rate - 0.003) * 100) 
    is_crashed = False
    
    if random.random() * 100 < crash_chance:
        is_crashed = True
        risk_penalty = 50.0
    else:
        risk_penalty = random.uniform(0, instability * 2.0)

    final_acc = base_score + potential_score - risk_penalty - (focus_violation_count * 5)
    final_acc = max(10.0, min(99.9, final_acc))
    
    if is_crashed:
        ui['print'](">> Validation Accuracy: NaN (Model Diverged)", "error")
        final_acc = 10.0
    else:
        steps_show = 8
        for i in range(steps_show):
            curr = final_acc * ((i+1)/steps_show) + random.uniform(-2, 2)
            curr = min(99.9, max(0, curr))
            ui['print'](f">> Validation Accuracy: {curr:.2f}%")
            time.sleep(0.1)
        
        color = "system"
        if final_acc >= 90: color = "success"
        elif final_acc < 60: color = "error"
        ui['print'](f">> FINAL ACCURACY: {final_acc:.2f}%", color)

    # ================= 4. 判定胜利条件 =================
    
    success = False
    fail_reason = ""

    if is_mission:
        req_acc = mission_reqs.get('target_acc')
        
        if req_acc is None:
            if is_crashed:
                success = False
                fail_reason = "Model Diverged"
            else:
                success = True
                ui['print']("[CONTRACT] Stability requirement met.", "success")
        else:
            if final_acc >= req_acc:
                success = True
                ui['print'](f"[CONTRACT] Target >{req_acc}% MET.", "success")
            else:
                success = False
                fail_reason = f"Accuracy {final_acc:.2f}% < Target {req_acc}%"
    else:
        if final_acc >= 60:
            success = True
        else:
            success = False
            fail_reason = "Accuracy too low (<60%)"
    rank_mult = 1.0
    if success:
        if final_acc >= 95: rank_mult = 1.5      # S Rank
        elif final_acc >= 85: rank_mult = 1.2    # A Rank
    # ================= 5. 发放奖励 =================
    
    final_coins = 0
    final_exp = 0
    total_minutes = (epochs * mins_per_epoch)
    result_payload = {
        "success": success,
        "accuracy": final_acc,
        "fail_reason": fail_reason,
        "rank_mult": rank_mult,
        "total_minutes": epochs * mins_per_epoch # 也可以把统计数据传回去
    }
    time.sleep(4)
    ui['set_mini_mode'](False)
    ui['finished'](result_payload)


def _make_progress_bar(percent, length=20):
    filled = int(length * percent / 100)
    # 使用标准 Block 字符，空余部分使用空格以匹配 PyTorch 默认风格
    # 如果你更喜欢原来的点状风格，可以把 " " 改回 "░"
    return "█" * filled + " " * (length - filled)

def _fmt(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"