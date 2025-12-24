import json
import os
import random
import uuid
import datetime
import time

class MissionGenerator:
    def __init__(self):
        # 1. 加载固定的剧情邮件 (emails.json)
        self.fixed_emails = self._load_json('emails.json')
        
        # 2. 定义随机任务的模板 (如果没有文件，就用代码里的默认池)
        self.random_senders = ["TechCorp", "Gamer123", "CryptoMiner", "StudioX"]
        self.random_topics = ["Optimization", "Data Cleaning", "Security Audit", "Beta Test"]

    def _load_json(self, filename):
        """通用 JSON 加载函数"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, 'data', filename)
        if not os.path.exists(path):
            print(f"[WARN] {filename} not found.")
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERR] Failed to load {filename}: {e}")
            return []

    def fetch_new_emails(self, game_data):
        """
        核心逻辑：
        1. 优先检查是否有触发的【固定剧情邮件】(emails.json)
        2. 如果没有剧情邮件，且冷却时间到了，生成【随机委托】
        """
        player_level = game_data.get('level', 1)
        current_gpu = game_data.get('gpu_level', 0)
        
        # 获取历史记录集合，方便 O(1) 查询
        received_ids = set(game_data.get('received_mail_ids', []))
        completed_ids = set(game_data.get('completed_mission_ids', []))
        
        new_batch = []

        # ==========================================
        # 1. 检查固定剧情任务 (emails.json)
        # ==========================================
        for email_tmpl in self.fixed_emails:
            mail_id = email_tmpl['id']
            
            # 过滤1: 已经收过了吗？
            if mail_id in received_ids:
                continue
            
            # 过滤2: 等级够了吗？
            if player_level < email_tmpl.get('req_level', 0):
                continue
                
            # 过滤3: 前置任务完成了吗？ (关键！)
            req_completed = email_tmpl.get('req_completed', [])
            if not all(rid in completed_ids for rid in req_completed):
                # 还有前置任务没做完，跳过
                continue

            # --- 条件满足，生成邮件 ---
            # 深度拷贝一份，防止修改原始模板
            email = self._process_story_email(email_tmpl)
            new_batch.append(email)
            
            # 剧情邮件通常一次只发一封，避免刷屏，或者你可以去掉 break 允许并发
            # break 

        # 如果生成了剧情邮件，通常就不再生成随机杂活了，让玩家专注剧情
        if new_batch:
            return new_batch

        # ==========================================
        # 2. 随机任务生成逻辑 (日常委托)
        # ==========================================
        
        # 检查冷却时间 (例如 60秒生成一次，开发测试期可以设短点)
        last_time = game_data.get('last_random_mission_time', 0)
        current_time = time.time()
        cooldown = 12*3600  # 生产环境建议 12*3600 (12小时)

        if current_time - last_time > cooldown and player_level >= 1:
            # 只有没有活跃任务时才发新的随机任务（可选策略）
            if not game_data.get('active_mission'):
                random_mail = self._generate_random_email(player_level, current_gpu)
                new_batch.append(random_mail)
                
                # 更新生成时间
                game_data['last_random_mission_time'] = current_time

        return new_batch

    def _process_story_email(self, template):
        """处理剧情邮件：填充动态时间，处理格式"""
        import copy
        mail = copy.deepcopy(template)
        
        # 补充必要字段
        mail['date'] = datetime.datetime.now().strftime("%H:%M")
        mail['read'] = False
        # 确保附件标记为非立即执行 (通常任务都需要训练)
        if 'attachment' in mail:
            if 'instant_action' not in mail['attachment']:
                mail['attachment']['instant_action'] = False
        
        return mail

    def _generate_random_email(self, player_level, gpu_level):
        """
        生成随机的日常任务
        这里保留了之前的代码逻辑，但更新了 rewards 格式适配新系统
        """
        sender_name = random.choice(self.random_senders)
        topic = random.choice(self.random_topics)
        
        difficulty = max(1, player_level + random.randint(-1, 1))
        base_ops = 100 * (1.2 ** difficulty)
        
        # 动态计算奖励
        reward_coin = int(40 * difficulty)
        reward_exp = int(80 * difficulty)

        # 构造符合新 RewardManager 的奖励列表
        rewards_list = [
            {"type": "exp", "val": reward_exp},
            {"type": "coin", "val": reward_coin}
        ]
        
        # 极低概率掉落物品 (示例)
        if random.random() < 0.05:
            rewards_list.append({"type": "item", "val": "mystery_box"})

        mail_id = f"rnd_{str(uuid.uuid4())[:6]}"
        
        return {
            "id": mail_id,
            "type": "random",
            "req_level": player_level,
            "sender": f"{sender_name} <auto@{sender_name.lower()}.net>",
            "subject": f"Contract: {topic} (Diff {difficulty})",
            "body": "System generated request.\nPerform the attached task for standard credits.",
            "date": datetime.datetime.now().strftime("%H:%M"),
            "read": False,
            "attachment": {
                "name": f"Task: {topic}",
                "base_ops": int(base_ops),
                "difficulty": difficulty,
                "requirements": {
                    "min_epochs": 5 + difficulty, 
                    "target_acc": 60 + (difficulty * 2)
                },
                "instant_action": False,
                "rewards": rewards_list  # <--- 注意这里用了 list
            }
        }