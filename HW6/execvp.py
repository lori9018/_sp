#!/usr/bin/env python3
"""
execvp.py - 示範 os.execvp() 系列函式

exec 系列函式會將當前行程的程式映像替換為新的程式，
因此 exec 之後的程式碼永遠不會被執行（除非 exec 失敗）。
"""

import os
import sys

def demo_execvp_ls():
    """用 execvp 執行 ls 指令"""
    print("=" * 50)
    print("[execvp] 將目前行程替換為 'ls -la'")
    print("  （以下為 ls 的輸出）\n")
    sys.stdout.flush()

    # execvp(name, args) — args[0] 習慣上是程式名稱
    os.execvp("ls", ["ls", "-la", "--color=auto"])

    # 這行永遠不會被執行（除非 exec 失敗）
    print("這裡不會被執行")


def demo_exec_failed():
    """exec 失敗的處理"""
    print("=" * 50)
    print("[exec 失敗] 執行不存在的指令")

    try:
        os.execvp("nonexistent_cmd", ["nonexistent_cmd"])
    except FileNotFoundError as e:
        print(f"  exec 失敗（預期）：{e}")


def demo_execvp_env():
    """使用 execvpe 傳遞環境變數"""
    print("=" * 50)
    print("[execvpe] 自訂環境變數執行指令")
    sys.stdout.flush()

    env = {"CUSTOM_VAR": "Hello_from_exec!", "PATH": os.environ.get("PATH", "")}
    os.execvpe("env", ["env"], env)
    # 執行 env 會印出所有環境變數，包含 CUSTOM_VAR


def demo_exec_in_child():
    """
    fork + exec 經典組合
    父行程繼續執行 Python，子行程變成其他程式
    """
    print("=" * 50)
    print("[fork + exec] 子行程變成 'echo Hello'")

    pid = os.fork()

    if pid == 0:
        # 子行程：把自己變成 echo
        os.execvp("echo", ["echo", "Hello from child process!"])
        # 如果 exec 失敗才到這裡
        sys.exit(1)
    else:
        # 父行程：等待子行程結束
        _, status = os.wait()
        print(f"  父行程: 子行程 (PID={pid}) 結束，status={status}")


def demo_shell_exec_simulation():
    """模擬 shell 的指令執行（fork + exec + wait）"""
    print("=" * 50)
    print("[簡易 shell 模擬]")

    commands = [
        ["echo", "Hello, 系統程式!"],
        ["whoami"],
        ["date"],
    ]

    for cmd in commands:
        pid = os.fork()
        if pid == 0:
            os.execvp(cmd[0], cmd)
            sys.exit(1)
        else:
            _, status = os.wait()
            print(f"  → 指令 '{' '.join(cmd)}' 執行完畢 (status={status})")


if __name__ == "__main__":
    # 注意: demo_execvp_ls() 和 demo_execvp_env() 會取代當前行程
    # 所以只能單獨執行它們，或 fork 後再 exec

    print("請選擇要執行的範例：")
    print("  1) fork + exec echo")
    print("  2) exec 失敗處理")
    print("  3) 模擬 shell 指令")
    print("  4) fork + exec env (自訂環境變數)")
    print("  5) exec ls（注意：會取代當前行程，無法返回）")

    choice = input("輸入選擇 (1-5): ").strip()

    if choice == "1":
        demo_exec_in_child()
    elif choice == "2":
        demo_exec_failed()
    elif choice == "3":
        demo_shell_exec_simulation()
    elif choice == "4":
        # 需 fork 避免 exec 取代主程式
        pid = os.fork()
        if pid == 0:
            demo_execvp_env()
        else:
            os.wait()
    elif choice == "5":
        demo_execvp_ls()  # 這會直接取代程式
    else:
        print("無效選擇")
