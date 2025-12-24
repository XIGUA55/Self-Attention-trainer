# module/shell_emulator.py
import os
import shlex
import shutil
import subprocess
import threading
from .storage import save_game_data

class ShellHandler:
    def __init__(self, terminal):
        self.term = terminal
        self.data = terminal.data
        self.root_dir = terminal.system_root

    def handle_ls(self, args):
        path = args[0] if args else "."
        try:
            files = sorted(os.listdir(path))
            self.term.write("\n")
            for f in files:
                if f.startswith(".") or f == "__pycache__": continue
                if os.path.isdir(f): self.term.write(f"{f:<15}", "dir")
                elif f.endswith(".py"): self.term.write(f"{f:<15}", "exe")
                else: self.term.write(f"{f:<15}")
                if (files.index(f) + 1) % 4 == 0: self.term.write("\n")
            self.term.write("\n")
        except Exception as e:
            self.term.write(f"ls: {e}\n", "error")

    def handle_cd(self, args):
        target = args[0] if args else self.root_dir
        try:
            target_path = os.path.abspath(os.path.join(os.getcwd(), target))
            if not target_path.startswith(self.root_dir):
                self.term.write(f"bash: cd: permission denied\n", "error")
            else:
                os.chdir(target_path)
        except Exception as e: self.term.write(f"cd: {e}\n", "error")

    def handle_sysctl(self, args):
        PARAM_MAP = {
            "kernel.focus_duration": "focus_duration",
            "kernel.strict_mode": "strict_mode"
        }

        if not args:
            for display_key, save_key in PARAM_MAP.items():
                val = self.data.get(save_key)
                if isinstance(val, bool): val = 1 if val else 0
                self.term.write(f"{display_key} = {val}\n")
        else:
            full_arg = "".join(args)
            if "=" in full_arg:
                key, val_str = full_arg.split("=", 1)
                if key not in PARAM_MAP:
                        self.term.write(f"sysctl: cannot stat /proc/sys/{key}: No such file or directory\n", "error")
                else:
                    save_key = PARAM_MAP[key]
                    try:
                        if save_key == "focus_duration":
                            new_val = int(val_str)
                            if new_val < 1: raise ValueError
                            self.data[save_key] = new_val
                            self.term.write(f"{key} = {new_val}\n")
                        elif save_key == "strict_mode":
                            is_true = val_str.lower() in ('1', 'on', 'true', 'yes')
                            self.data[save_key] = is_true
                            self.term.write(f"{key} = {1 if is_true else 0}\n")
                        save_game_data(self.data)
                    except ValueError:
                            self.term.write(f"sysctl: invalid value '{val_str}' for key '{key}'\n", "error")
            else:
                key = full_arg
                if key in PARAM_MAP:
                    val = self.data.get(PARAM_MAP[key])
                    if isinstance(val, bool): val = 1 if val else 0
                    self.term.write(f"{key} = {val}\n")
                else:
                    self.term.write(f"sysctl: cannot stat /proc/sys/{key}: No such file or directory\n", "error")

    def run_external_cmd(self, cmd_str):
        """运行外部系统命令 (原 run_system_cmd)"""
        def _task():
            parts = shlex.split(cmd_str)
            if not parts: 
                self.term.after(0, self.term.new_prompt)
                return
            cmd_head = parts[0]
            
            SHELL_BUILTINS = {
                'dir', 'echo', 'type', 'copy', 'del', 'ren', 'rename', 'move', 
                'mkdir', 'md', 'rmdir', 'rd', 'cls', 'ver', 'vol', 'date', 'time', 
                'set', 'path', 'assoc', 'start', 'call', 'attrib'
            }
            
            has_shell_chars = any(c in cmd_str for c in ['|', '<', '>', '&', '^'])
            
            # 快速检查，避免不必要的 subprocess 调用
            if not has_shell_chars and \
               cmd_head.lower() not in SHELL_BUILTINS and \
               shutil.which(cmd_head) is None and \
               not os.path.exists(cmd_head):
                
                err_msg = f"bash: {cmd_head}: command not found\n"
                self.term.after(0, lambda: self.term.write(err_msg, "error"))
                self.term.after(0, self.term.new_prompt)
                return

            try:
                # 注意：这里我们使用 self.term.write，但需要在主线程更新 UI
                # TerminalCore 的 write 方法通常是线程安全的(after调用)，或者是直接操作 UI
                # 如果 TerminalCore.write 内部用了 after，这里直接调没问题。
                # 你的代码原版是用 self.after(0, ...) 包装的，这里保持一致。

                process = subprocess.Popen(
                    cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                    text=True, bufsize=1, errors='replace'
                )
                
                def read_stream(stream, is_error=False):
                    for line in iter(stream.readline, ''):
                        if line:
                            if is_error:
                                if "不是内部或外部命令" in line or "is not recognized" in line:
                                    msg = f"bash: {cmd_head}: command not found\n"
                                    self.term.after(0, lambda: self.term.write(msg, "error"))
                                else:
                                    self.term.after(0, lambda l=line: self.term.write(l, "error"))
                            else:
                                self.term.after(0, lambda l=line: self.term.write(l))
                    stream.close()

                t_out = threading.Thread(target=read_stream, args=(process.stdout, False))
                t_err = threading.Thread(target=read_stream, args=(process.stderr, True))
                t_out.start()
                t_err.start()

                process.wait()
                t_out.join()
                t_err.join()
                        
            except Exception as e:
                self.term.after(0, lambda: self.term.write(str(e) + "\n", "error"))
            
            self.term.after(0, self.term.new_prompt)
            
        threading.Thread(target=_task, daemon=True).start()