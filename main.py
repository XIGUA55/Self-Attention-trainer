import os
import shlex
import time
import random

# 引入 TUI 核心
from module.TUI import TerminalCore

# 引入业务逻辑
from module.config import HARDWARE
from module.storage import load_game_data, save_game_data
from module.file_manager import init_workspace
import data.assets as assets
from module.mail_system import MailSystem 
import module.train as train_system
from data.manuals import COMMAND_LIST, get_man_page
from module.game_mechanics import RewardManager
# [新增] 引入分离出去的模块
from module.shop import ShopHandler
from module.shell_emulator import ShellHandler

class CyberTerminal(TerminalCore):
    def __init__(self):
        super().__init__(title="Self-Attention-trainer_Terminal", width=960, height=480)
        self.attributes('-topmost', False)
        
        # 1. 基础数据加载
        self.data = load_game_data()
        init_workspace()
        try: os.chdir(self.system_root)
        except: pass

        # 2. 初始化各子系统
        self.mail_sys = MailSystem(self.data)
        self.reward_manager = RewardManager(self)
        self.active_mission = self.data.get('active_mission', None)
        
        # [新增] 初始化处理句柄
        self.shop_handler = ShopHandler(self)
        self.shell_handler = ShellHandler(self)

        self.interaction_mode = None
        self.temp_train_options = {}
        self.temp_selected_model = None

        # 3. 启动任务
        self.after(200, self.boot_sequence)

    def _auto_check_mail(self):
        """后台静默检查邮件"""
        count = self.mail_sys.check_for_new_mail()
        if count > 0:
            self.write(f"\n[Notification] You have {count} new mail(s). Type 'mail' to view.\n", "success")
            save_game_data(self.data)

    # ================= 窗口模式控制 =================
    
    def set_mini_mode(self, enable=True):
        if enable:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            self.geometry(f"400x100+{screen_width-450}+{screen_height-200}")
            self.attributes('-topmost', True)
            self.console.configure(font=("Consolas", 10))
        else:
            self.geometry("960x480")
            self.attributes('-topmost', False)
            self.console.configure(font=("Consolas", 14))

    # ================= 输入处理 =================

    def on_user_input(self, user_input):
        if self.interaction_mode == 'train_model':
            self.handle_train_model_selection(user_input)
        elif self.interaction_mode == 'train_epochs':
            self.handle_train_epochs_input(user_input)
        else:
            if user_input: self.process_command(user_input)
            else: self.new_prompt()

    # ================= 核心命令路由 =================

    def process_command(self, cmd_str):
        parts = shlex.split(cmd_str)
        if not parts: 
            self.new_prompt()
            return  
        cmd = parts[0].lower()
        args = parts[1:]

        # --- 基础系统命令 (Exit, Clear, Help) ---
        if cmd == "exit":
            self.quit()
        elif cmd in ["clear", "cls"]:
            self.clear_screen()
            self.print_motd()
            self.new_prompt()
        elif cmd == "help":
            self._handle_help(args)
            self.new_prompt()
            
        # --- Shell 文件命令 (ls, cd, sysctl) -> 委托给 ShellHandler ---
        elif cmd == "ls":
            self.shell_handler.handle_ls(args)
            self.new_prompt()
        elif cmd == "cd":
            self.shell_handler.handle_cd(args)
            self.new_prompt()
        elif cmd == "sysctl":
            self.shell_handler.handle_sysctl(args)
            self.new_prompt()

        # --- 商店命令 (Shop, Buy) -> 委托给 ShopHandler ---
        elif cmd == "shop":
            self.shop_handler.show_shop()
            self.new_prompt()
        elif cmd == "buy":
            self.shop_handler.buy_item(args)
            self.new_prompt()

        # --- 邮件与任务命令 (Mail, Read, Accept) ---
        elif cmd in ["mail", "read", "accept"]:
            self._handle_mail_commands(cmd, args)
            self.new_prompt()

        # --- 训练命令 (Train) ---
        elif cmd == "train":
            self._initiate_training_sequence()
            # 注意：这里不调用 new_prompt，因为进入了交互模式

        # --- 外部命令 ---
        else:
            self.shell_handler.run_external_cmd(cmd_str)
            # 注意：run_external_cmd 会在线程结束后自己调用 new_prompt

    # ================= 辅助逻辑封装 =================

    def _handle_help(self, args):
        if not args:
            self.write("\nGNU bash, version 5.1.16(1)-release (x86_64-pc-linux-gnu)\n")
            self.write("Type 'help name' to find out more about the function 'name'.\n\n")
            for name, desc in COMMAND_LIST:
                self.write(f" {name:<10} {desc}\n")
            self.write("\n")
        else:
            page = get_man_page(args[0].lower())
            if page: self.write(page + "\n")
            else: self.write(f"bash: help: no help topics match '{args[0]}'.\n", "error")

    def _handle_mail_commands(self, cmd, args):
        if cmd == "mail":
            if args and args[0] == "check":
                count = self.mail_sys.check_for_new_mail()
                if count > 0:
                    self.write(f"Synced {count} new message(s).\n", "success")
                    save_game_data(self.data)
                else: self.write("No new messages on server.\n", "dim")
            else:
                inbox = self.mail_sys.get_inbox()
                self.write("\n--- INBOX ---\n", "system")
                if not inbox: self.write("  (No messages)\n", "dim")
                else:
                    self.write(f" {'ID':<10} {'Sender':<25} {'Subject':<35} {'Flags'}\n")
                    self.write("-" * 80 + "\n")
                    for m in inbox:
                        style = "warn" if m.get('type') == 'story' else None
                        status = "[NEW]" if not m['read'] else "    "
                        self.write(f" {m['id']:<10} {m['sender']:<25} {m['subject']:<35} {status}\n", style)
                self.write("\nUse 'read <id>' to view details.\n")

        elif cmd == "read":
            if not args: return self.write("Usage: read <mail_id>\n", "error")
            mail = self.mail_sys.get_mail(args[0])
            if mail:
                self.mail_sys.mark_as_read(args[0])
                save_game_data(self.data) 
                self.write(f"\nFrom:    {mail['sender']}\nDate:    {mail['date']}\nSubject: {mail['subject']}\n")
                self.write("-" * 60 + "\n" + mail['body'] + "\n" + "-" * 60 + "\n")
                if 'attachment' in mail:
                    att = mail['attachment']
                    self.write(f"[ATTACHMENT] {att['name']}\n", "warn")
                    self.write(f"  Rewards: {att['rewards']['exp']} XP, ${att['rewards']['coin']}\n", "dim")
                    self.write(f"Type 'accept {args[0]}' to download mission data.\n")
            else: self.write(f"Mail ID '{args[0]}' not found.\n", "error")

        elif cmd == "accept":
            if not args: return self.write("Usage: accept <mail_id>\n", "error")
            
            mail = self.mail_sys.get_mail(args[0])
            if not mail or 'attachment' not in mail:
                return self.write("Cannot accept: Mail not found or no attachment.\n", "error")

            att = mail['attachment']

            # [新增] 检查是否为硬件升级包
            if att.get('instant_action', False):
                self.reward_manager.apply_rewards(att.get('rewards', []))
                self.mail_sys.delete_mail(args[0])
                save_game_data(self.data)
                return

            # 2. 如果不是立即执行，则是任务，放入 active_mission
            if self.active_mission: 
                return self.write("Error: Active mission exists.\n", "error")
            
            self.active_mission = att
            self.active_mission['source_mail_id'] = args[0]
            # ... 保存逻辑 ...
            self.write(f"Mission '{self.active_mission['name']}' downloaded.\n", "success")
        else: self.write("Cannot accept: Mail not found or no attachment.\n", "error")

    def _initiate_training_sequence(self):
        menu_lines, options = train_system.get_menu_data(self.data)
        self.write("\n")
        
        # 注入活跃任务
        if self.active_mission:
            m = self.active_mission
            self.write(">>> ACTIVE ASSIGNMENT <<<\n", "warn")
            self.write(f" [0] {m['name']} (Req: {m['requirements']})\n")
            self.write("-" * 40 + "\n")
            
            current_hw = HARDWARE[min(self.data.get('gpu_level', 0), len(HARDWARE)-1)]
            tflops = max(0.1, current_hw['tflops'])
            
            options['0'] = {
                "model": {
                    "name": m['name'], "base_ops": m['base_ops'], "difficulty": m['difficulty'],
                    "__mission_reqs": m['requirements'], "__rewards": m['rewards'], "max_loss": 2.5
                },
                "mins_per_epoch": (m['base_ops'] / tflops) * 0.05,
                "auto_epochs": m['requirements'].get('min_epochs') or 10
            }

        for line in menu_lines: self.write(line + "\n")
        self.write("\n")
        self.temp_train_options = options
        self.interaction_mode = 'train_model'
        self.new_prompt(custom_text="Select ID (0 for mission, 1+ for custom): ")

    # ================= 交互状态处理 (保持不变) =================

    def handle_train_model_selection(self, user_input):
        if not user_input: user_input = "1"
        if user_input in self.temp_train_options:
            self.temp_selected_model = self.temp_train_options[user_input]
            default_eps = self.temp_selected_model['auto_epochs']
            self.interaction_mode = 'train_epochs'
            self.new_prompt(custom_text=f"Epochs [default: {default_eps}]: ")
        else:
            self.write(f"bash: {user_input}: invalid model ID\n", "error")
            self.interaction_mode = None
            self.new_prompt()

    def handle_train_epochs_input(self, user_input):
        def on_training_complete(result):
            """
            result 结构示例: 
            {'success': True, 'accuracy': 95.5, 'rank_mult': 1.5, 'fail_reason': None}
            """
            self.lock_input(False)
            self.interaction_mode = None
            
            # 1. 显示结果
            if result['success']:
                self.write(f"\n[RESULT] Training Success! Acc: {result['accuracy']:.2f}%\n", "success")
                
                # 2. 如果是任务，从 active_mission 获取奖励定义
                if self.active_mission:
                    rewards = self.active_mission.get('rewards', [])
                    # 调用通用管理器发奖
                    self.reward_manager.apply_rewards(rewards, multiplier=result.get('rank_mult', 1.0))
                    mission_id = self.active_mission.get('source_mail_id')
                    if mission_id:
                        completed_list = self.data.get('completed_mission_ids', [])
                        if mission_id not in completed_list:
                            completed_list.append(mission_id)
                            self.data['completed_mission_ids'] = completed_list
                    # 清理任务
                    self.active_mission = None
                    self.data['active_mission'] = None
                    
                    self.write("[SYSTEM] Mission closed.\n", "dim")
                
                # 3. 如果是自由训练 (没有 active_mission)，生成通用奖励
                else:
                    # 这里也可以用 RewardManager，临时生成一个奖励列表
                    gen_rewards = [
                        {"type": "coin", "val": 10}, # 基础值
                        {"type": "exp", "val": 20}
                    ]
                    self.reward_manager.apply_rewards(gen_rewards, multiplier=result.get('rank_mult', 1.0))

            else:
                self.write(f"\n[FAILED] {result['fail_reason']}\n", "error")
                # 失败安慰奖
                self.reward_manager.apply_rewards([{"type": "exp", "val": 10}])

            save_game_data(self.data)
            self.new_prompt()
        callbacks = {
            'print': lambda t, s=None: self.after(0, lambda: self.write(str(t)+"\n", s)),
            'update_bar': lambda t: self.after(0, lambda: self._ui_update_bar(t)),
            'set_mini_mode': lambda val: self.after(0, lambda: self.set_mini_mode(val)),
            # 这里的 finished 不再只是 UI 复位，而是携带数据的业务回调
            'finished': lambda res: self.after(0, lambda: on_training_complete(res))
        }
        self.lock_input(True)
        train_system.start_training_session(..., callbacks)

    def _ui_update_bar(self, text):
        self.tk_text.delete("end-1c linestart", "end-1c")
        self.write(text)

    def _ui_train_finished(self):
        self.lock_input(False)
        self.interaction_mode = None
        self.new_prompt()

    # ================= 开机动画 =================

    def boot_sequence(self):
        self.lock_input(True)
        for log in assets.BOOT_LOGS[:6]:
            self.write(log + "\n", "dim")
            self.update()
            time.sleep(0.01)
        for service in assets.BOOT_SERVICES:
            self.write(f"[  OK  ] Started {service}.\n")
            self.update()
            time.sleep(random.uniform(0.02, 0.08))
            
        time.sleep(0.5)
        self.clear_screen()
        self.write("Ubuntu 22.04.2 LTS cyber-node-01 tty1\n\n")
        self.write("cyber-node-01 login: ", "system")
        self.update()
        time.sleep(0.5)
        self.write("root\n")
        time.sleep(0.3)
        self.write("Password: ")
        time.sleep(0.5)
        self.write("\n\n")
        self.print_motd()
        self.after(200, self._auto_check_mail)
        self.new_prompt()

    def print_motd(self):
        gpu = HARDWARE[min(self.data.get('gpu_level', 0), len(HARDWARE)-1)]
        self.write(f"Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-76-generic x86_64)\n\n")
        self.write(f"  System load:  0.08              Processes: 104\n")
        self.write(f"  Memory usage: 24%               IPv4 address: 192.168.1.42\n")
        self.write(f"  GPU Driver:   NVIDIA 535.54     GPU: {gpu['name']}\n\n")
        self.write(f"  => Compute Credits: ${self.data.get('coins', 0)}\n", "warn")

if __name__ == "__main__":
    app = CyberTerminal()
    app.mainloop()