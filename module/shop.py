# module/shop.py
from .config import HARDWARE
from .storage import save_game_data

class ShopHandler:
    def __init__(self, terminal):
        self.term = terminal  # 持有终端实例以便输出
        self.data = terminal.data

    def show_shop(self):
        self.term.write("\n--- HARDWARE MARKET ---\n", "system")
        
        current_idx = self.data.get('gpu_level', 0)
        current_idx = min(current_idx, len(HARDWARE) - 1)
        current_hw = HARDWARE[current_idx]
        
        # 设定可见上限：当前等级 + 1
        visible_cap = current_hw.get('level', 1) + 1

        # 打印表头
        header = f"{'No.':<4} {'Lv.':<4} {'Name':<32} {'TFLOPS':<10} {'Cost'}"
        self.term.write(header + "\n")
        self.term.write("-" * 65 + "\n") 

        for i, h in enumerate(HARDWARE):
            if h['level'] <= visible_cap:
                is_owned = (i == current_idx)
                prefix = "*" if is_owned else " "
                idx_display = f"{prefix}{i}" 
                
                row_str = f"{idx_display:<4} {h['level']:<4} {h['name']:<32} {h['tflops']:<10} ${h['cost']}"
                
                style = "system" if is_owned else None
                self.term.write(row_str + "\n", style)
                self.term.write(f"      {h['description']}\n", "dim")
                self.term.write("\n") 

    def buy_item(self, args):
        if not args:
             self.term.write("Usage: buy <id>\n", "error")
             return
             
        item_id = args[0]
        found = False
        
        for i, h in enumerate(HARDWARE):
            if str(i) == item_id or str(h['id']) == item_id:
                found = True
                if self.data['coins'] >= h['cost']:
                    # 禁止降级
                    if i < self.data.get('gpu_level', 0):
                         self.term.write("Downgrading hardware is not allowed.\n", "error")
                         return
                    
                    self.data['coins'] -= h['cost']
                    self.data['gpu_level'] = i
                    save_game_data(self.data)
                    self.term.write(f"Purchased {h['name']}.\n", "success")
                else:
                    self.term.write(f"Transaction failed: Insufficient funds (Need ${h['cost']}).\n", "error")
                break
        
        if not found: self.term.write(f"Item ID {item_id} not found.\n", "error")