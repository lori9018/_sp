#!/usr/bin/env python3
"""
HW6 系統程式 — 範例總入口

執行此腳本可選擇觀看各個主題的示範。
"""

import os
import sys

MENU = """
╔══════════════════════════════════════════╗
║    HW6 — 行程與檔案系統程式示範          ║
╠══════════════════════════════════════════╣
║  1) fork.py        — 行程建立           ║
║  2) execvp.py      — 行程替換           ║
║  3) file_ops.py    — 檔案操作           ║
║  4) dup2.py        — 重新導向           ║
║  5) pipe_redirect.py — 管線與組合範例    ║
║  q) 離開                                ║
╚══════════════════════════════════════════╝
"""

SCRIPTS = {
    "1": "fork.py",
    "2": "execvp.py",
    "3": "file_ops.py",
    "4": "dup2.py",
    "5": "pipe_redirect.py",
}

if __name__ == "__main__":
    while True:
        print(MENU)
        choice = input("選擇一個範例執行 (1-5) 或 q 離開: ").strip().lower()

        if choice == "q":
            print("Bye!")
            sys.exit(0)

        if choice in SCRIPTS:
            script = SCRIPTS[choice]
            pid = os.fork()
            if pid == 0:
                os.execvp("python", ["python", script])
                sys.exit(1)
            else:
                os.wait()
        else:
            print("無效選擇，請重試")
