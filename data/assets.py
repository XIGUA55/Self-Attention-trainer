# assets.py
# 存放纯静态的文本资源，让主程序更清爽

# Linux 内核启动日志
BOOT_LOGS = [
    "[    0.000000] Linux version 5.15.0-76-generic (buildd@lcy02-amd64-024) (gcc (Ubuntu 11.3.0) 11.3.0)",
    "[    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-5.15.0-76-generic root=UUID=0000 ro quiet splash",
    "[    0.004211] Console: colour dummy device 80x25",
    "[    0.452112] ACPI: Core revision 20210930",
    "[    1.213000] Run /init as init process",
    "[    1.521231] systemd[1]: Detected architecture x86-64.",
    "[    1.892100] systemd[1]: Set hostname to <cyber-node-01>.",
    "[    2.100231] wlp3s0: link becomes ready",
    "[    2.451201] IPv6: ADDRCONF(NETDEV_CHANGE): wlp3s0: link becomes ready"
]

# 启动服务列表
BOOT_SERVICES = [
    "Load/Save Random Seed",
    "Apply Kernel Variables",
    "CyberFocus Neural Engine", 
    "NVIDIA Persistence Daemon",
    "System Logging Service",
    "Permit User Sessions",
    "Docker Application Container Engine",
    "Unattended Upgrades Shutdown"
]