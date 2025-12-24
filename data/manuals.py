
# manuals.py

# 帮助命令概览 (命令名称, 简短描述)
COMMAND_LIST = [
    ("help", "Display information about builtin commands"),
    ("train", "Start an interactive training session (Focus Mode)"),
    ("mail", "Check inbox for client missions"),
    ("accept", "Accept a mission from the inbox"),
    ("shop", "View available hardware upgrades"),
    ("buy", "Purchase hardware from the repository"),
    ("ls", "List directory contents"),
    ("cd", "Change the shell working directory"),
    ("clear", "Clear the terminal screen"),
    ("exit", "Logout and close the session"),
    ("sysctl", "Configure kernel parameters (e.g. Focus Time)")
]

# 详细 Man Pages
_MAN_PAGES = {
    "help": """
NAME
    help - Display information about builtin commands.

SYNOPSIS
    help [pattern ...]

DESCRIPTION
    Displays a brief summary of builtin commands. If pattern is specified,
    gives detailed help on all commands matching pattern.
""",
    "sysctl": """
NAME
    sysctl - configure kernel parameters at runtime

SYNOPSIS
    sysctl [variable]
    sysctl -w [variable]=[value]

DESCRIPTION
    Used to modify game settings (Kernel Parameters).

EXAMPLES
    Check current focus time:
      sysctl kernel.focus_duration

    Set focus time to 45 minutes:
      sysctl -w kernel.focus_duration=45
""",
    "train": """
NAME
    train - CyberFocus Interactive Task Scheduler

SYNOPSIS
    train [options]

DESCRIPTION
    Launches the TUI (Text User Interface) for selecting Deep Learning models.
    
    Training consumes time (Focus Mode).
    Successful training grants:
      - Credits (Coins)
      - Experience (Exp) for Level Up
    
    WARNING:
    High epoch counts on low-level accounts may lead to Overfitting risks.
""",
    "shop": """
NAME
    shop - Hardware Package Repository

DESCRIPTION
    Lists all available GPU accelerators (NVIDIA/TPU) available for purchase.
    Better hardware increases TFLOPS, reducing training time per epoch.
""",
    "buy": """
NAME
    buy - Install new hardware packages

SYNOPSIS
    buy [package_id]

EXAMPLE
    buy 1      # buy GTX 1080 Ti
    buy 3      # buy NVIDIA A100
    *found package_id in shop list*
""",
    "mail": """
NAME
    mail - Check your message from your professor or client

DESCRIPTION
    Sometimes you will receive mission contracts or just messages from your professor.
    Check your inbox regularly to not miss any important updates.
""",
    "accept": """
NAME
    accept - Confirm mission contract

SYNOPSIS
    accept [JOB_ID]

DESCRIPTION
    Accepts a specific job ID from the mail list. 
    Once accepted, training that specific model will yield contract rewards.
""",
    "ls": """
NAME
    ls - list directory contents

DESCRIPTION
    List information about the FILEs (the current directory by default).
""",
    "cd": """
NAME
    cd - change the shell working directory

SYNOPSIS
    cd [dir]

DESCRIPTION
    Change the current directory to DIR. The default DIR is the system root.
""",
    "clear": """
NAME
    clear - clear the terminal screen

DESCRIPTION
    Clears your screen if this is possible, including its scrollback buffer.
""",
    "exit": """
NAME
    exit - cause the shell to exit

DESCRIPTION
    Exits the CyberTerminal session.
"""
}

def get_man_page(command):
    """获取指定命令的帮助文档，如果不存在则返回 None"""
    return _MAN_PAGES.get(command, None)