import json
import os
import random
import uuid
import datetime
import time  # [新增] 引入 time 模块用于处理时间戳

class MissionGenerator:
    def __init__(self):
        self.fixed_emails = self._load_fixed_emails()
        
        # 外部客户池 (只有 GPU >= 4 才会解锁)
        self.external_senders = ["TechCorp", "Gamer123", "CryptoMiner", "StudioX", "DeepMind-Clone"]
        self.external_topics = ["Optimization", "Data Cleaning", "Security Audit", "Beta Test"]
        
        # 教授的任务课题
        self.professor_topics = ["Academic Research", "Algorithm Calibration", "Lab Assistant Task", "Thesis Data Crunching"]

    def _load_fixed_emails(self):
        """加载外部 JSON 文件"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, 'data', 'emails.json')
        if not os.path.exists(path): return []
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []

    def fetch_new_emails(self, game_data):
        """
        核心逻辑：根据玩家状态决定生成什么邮件
        """
        player_level = game_data.get('level', 1)
        current_gpu_level = game_data.get('gpu_level', 0)
        history = set(game_data.get('received_mail_ids', []))
        
        new_batch = []

        # ==========================================
        # 逻辑 1: 显卡升级事件检测 (Level 2, 3, 4)
        # 优先级最高：如果有升级，先发升级邮件，不进行随机任务判定
        # ==========================================
        if player_level > current_gpu_level+1 and current_gpu_level < 4:
            next_gpu_level = current_gpu_level + 1
            upgrade_id = f"upgrade_{next_gpu_level}"
            
            if upgrade_id not in history:
                upgrade_email = self._create_upgrade_email(next_gpu_level, upgrade_id)
                new_batch.append(upgrade_email)
                return new_batch

        # ==========================================
        # 逻辑 2: 固定剧情邮件
        # ==========================================
        for email in self.fixed_emails:
            if email['id'] not in history and player_level >= email['req_level']:
                email_copy = email.copy()
                email_copy['date'] = datetime.datetime.now().strftime("%H:%M")
                email_copy['read'] = False
                email_copy['type'] = 'story' 
                new_batch.append(email_copy)
        
        # ==========================================
        # 逻辑 3: 随机委托生成 (加入时间控制)
        # ==========================================
        
        # 获取上次生成时间 (如果不存在则为0)
        last_gen_time = game_data.get('last_random_mission_time', 0)
        current_time = time.time()
        
        # 设定冷却时间：12小时 (秒)
        # 调试建议：测试时可以将 12*3600 改为 10 (10秒) 以便快速验证
        cooldown = 12 * 3600 
        
        # 只有当 (当前时间 - 上次时间 >= 12小时) 且没有正在处理的剧情邮件时才生成
        if (current_time - last_gen_time >= cooldown) and player_level >= 1:
            
            # 随机生成 1 到 2 个任务
            mission_count = random.randint(1, 2)
            
            for _ in range(mission_count):
                random_mail = self._generate_random_email(player_level, current_gpu_level)
                new_batch.append(random_mail)
            
            # [关键] 更新生成时间戳并记录到 game_data
            game_data['last_random_mission_time'] = current_time
            # 注意：这里的 game_data 是引用，修改后会在 mail_system 保存时写入硬盘

        return new_batch

    def _create_upgrade_email(self, target_level, mail_id):
        """生成特殊的硬件升级邮件"""
        return {
            "id": mail_id,
            "type": "upgrade",
            "sender": "Professor",
            "subject": f"Hardware Upgrade Notification: Level {target_level}",
            "body": f"Excellent progress. I have authorized a hardware upgrade for your node.\n\n"
                    f"Accept this attachment to install the [Level {target_level} GPU] driver patch.\n"
                    f"Keep up the good work.",
            "date": datetime.datetime.now().strftime("%H:%M"),
            "read": False,
            "attachment": {
                "name": f"Driver Patch v{target_level}.0",
                # 新增字段：标记这是一个立即生效的动作，不需要训练
                "instant_action": True, 
                # 标准化奖励列表
                "rewards": [
                    {"type": "gpu_level", "val": target_level}
                ]
        }
        }

    def _generate_random_email(self, player_level, gpu_level):
        """随机生成逻辑 (根据显卡等级区分待遇)"""
        
        # --- 根据 GPU 等级决定发件人和奖励 ---
        if gpu_level < 4:
            # === 导师带教阶段 (Level < 4) ===
            sender_name = "Professor"
            sender_email = "lab_director@university.edu"
            mission_flavor = random.choice(["Commercial", "Tutorial"])
            topic = random.choice(self.professor_topics)
            
            if mission_flavor == "Commercial":
                subject = f"Assigment: External Request ({topic})"
                body = "I received this request from a partner. It's a good practice opportunity.\n" \
                       " Complete the attached task to gain some experience from this job."
            else:
                subject = f"Tutorial: {topic} Basics"
                body = "Here is a standard dataset. Practice your tuning parameters."
            
            reward_coin = 0
            reward_exp_mult = 1.2
            
        else:
            # === 独立接单阶段 (Level >= 4) ===
            choice = random.choice(self.external_senders)
            sender_name = choice
            sender_email = f"auto@{choice.lower()}.net"
            topic = random.choice(self.external_topics)
            
            subject = f"Contract: {topic} v.{random.randint(1,9)}"
            body = "System generated request.\nPerform the attached task for standard credits."
            
            reward_coin = 40
            reward_exp_mult = 1.0

        # --- 通用数值计算 ---
        difficulty = max(1, player_level + random.randint(-1, 1))
        base_ops = 100 * (1.2 ** difficulty)
        rnd_id = f"rnd_{str(uuid.uuid4())[:6]}"
        rewards_list = [
            {"type": "exp", "val": int(80 * difficulty * reward_exp_mult)},
            {"type": "coin", "val": int(reward_coin * difficulty)}
        ]
        return {
            "id": rnd_id,
            "type": "random",
            "req_level": player_level,
            "sender": f"{sender_name} <{sender_email}>",
            "subject": subject,
            "body": body,
            "date": datetime.datetime.now().strftime("%H:%M"),
            "read": False,
            "attachment": {
                "name": f"Task: {topic}",
                "base_ops": int(base_ops),
                "difficulty": difficulty,
                "requirements": { ... },
                "instant_action": False, # 需要训练
                "rewards": rewards_list # 使用列表替代原来的 dict
            }
        }