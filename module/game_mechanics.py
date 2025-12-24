# module/game_mechanics.py

class RewardManager:
    def __init__(self, terminal_ref):
        """
        terminal_ref: 传入 main.py 中的 CyberTerminal 实例，
        以便我们可以访问 self.data 和 UI 输出方法 (self.write)
        """
        self.term = terminal_ref
        
        # 注册所有支持的奖励类型处理函数
        self.handlers = {
            "coin": self._add_coin,
            "exp": self._add_exp,
            "gpu_level": self._upgrade_gpu,
            "item": self._add_item,
            # 未来可以轻松扩展:
            # "unlock_cmd": self._unlock_command,
            # "trigger_story": self._trigger_story
        }

    def apply_rewards(self, reward_list, multiplier=1.0):
        """
        通用的奖励分发入口
        reward_list: list of dict, e.g. [{"type": "coin", "val": 100}, ...]
        multiplier: 用于表现评分 (Rank S 1.5倍奖励)
        """
        if not reward_list:
            return

        self.term.write("\n[SYSTEM] Processing Rewards...\n", "system")
        
        for reward in reward_list:
            r_type = reward.get('type')
            r_val = reward.get('val')
            
            if r_type in self.handlers:
                # 执行对应的处理函数
                handler = self.handlers[r_type]
                handler(r_val, multiplier)
            else:
                self.term.write(f"  [ERR] Unknown reward type: {r_type}\n", "error")

        # 统一处理升级检查 (不再写死在 train.py)
        self._check_level_up()

    # --- 具体实现 ---

    def _add_coin(self, value, mult):
        final_val = int(value * mult)
        self.term.data['coins'] = self.term.data.get('coins', 0) + final_val
        self.term.write(f"  > Credits transferred: +${final_val}\n", "success")

    def _add_exp(self, value, mult):
        # 经验值通常不乘倍率，或者你需要的话也可以乘
        final_val = int(value) 
        self.term.data['Exp'] = self.term.data.get('Exp', 0) + final_val
        self.term.write(f"  > Data Sync: +{final_val} XP\n", "success")

    def _upgrade_gpu(self, target_level, _):
        # 硬件升级通常忽略倍率
        self.term.data['gpu_level'] = target_level
        self.term.write(f"  > [HARDWARE] GPU upgraded to Level {target_level}!\n", "warn")

    def _add_item(self, item_id, _):
        # 示例：添加到背包
        inventory = self.term.data.get('inventory', [])
        inventory.append(item_id)
        self.term.data['inventory'] = inventory
        self.term.write(f"  > Item acquired: {item_id}\n", "system")

    def _check_level_up(self):
        # 从 train.py 移出来的升级逻辑
        while True:
            current_lv = self.term.data.get('level', 1)
            req_exp = ((current_lv+1)**2) * 100
            current_exp = self.term.data.get('Exp', 0)
            
            if current_exp >= req_exp:
                self.term.data['Exp'] -= req_exp
                self.term.data['level'] += 1
                self.term.write(f"  *** LEVEL UP! -> Lv.{current_lv + 1} ***\n", "warn")
            else:
                break