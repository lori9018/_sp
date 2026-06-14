#!/usr/bin/env python3
"""
fork.py - 示範 os.fork() 建立行程

fork() 會複製當前行程，產生一個子行程。
父行程與子行程從同一點繼續執行，但 fork() 回傳值不同。
"""

import os
import sys
import time

def demo_basic_fork():
    """基本 fork 示範"""
    print("=" * 50)
    print("[基本 fork] 建立子行程")
    print(f"  父行程 PID: {os.getpid()}")

    pid = os.fork()

    if pid == 0:
        # 子行程 (fork 回傳 0)
        print(f"  → 子行程: PID={os.getpid()}, 父PID={os.getppid()}")
        sys.exit(0)  # 子行程結束
    else:
        # 父行程 (fork 回傳子行程 PID)
        print(f"  → 父行程: 子行程 PID={pid}")
        os.wait()  # 等待子行程結束
    print()

def demo_fork_shared_vs_copy():
    """
    fork 後變數複製 — 父子行程各自獨立
    寫入時複製 (Copy-on-Write)
    """
    print("=" * 50)
    print("[寫入時複製] 變數在 fork 後各自獨立")

    counter = 0
    pid = os.fork()

    if pid == 0:
        # 子行程: 修改自己的 counter
        counter += 10
        print(f"  子行程: counter = {counter} (位址: {id(counter)})")
        sys.exit(0)
    else:
        # 父行程: counter 不受子行程影響
        counter += 1
        print(f"  父行程: counter = {counter} (位址: {id(counter)})")
        os.wait()
    print()

def demo_fork_orphan():
    """孤兒行程 — 父行程先結束，子行程被 init 收養"""
    print("=" * 50)
    print("[孤兒行程] 父行程先結束，子行程被 init 收養")

    pid = os.fork()

    if pid == 0:
        # 子行程: 睡一會讓父行程先結束
        time.sleep(2)
        print(f"  子行程: PID={os.getpid()}, 現在父PID={os.getppid()}")
        sys.exit(0)
    else:
        print(f"  父行程: PID={os.getpid()}, 我先走了")
        sys.exit(0)  # 父行程直接結束
    # 注意：父行程結束後，子行程的 ppid 會變成 1 (init)


def demo_fork_zombie():
    """殭屍行程 — 子行程結束但父行程未呼叫 wait()"""
    print("=" * 50)
    print("[殭屍行程] 父行程未 wait → 子行程變殭屍")

    pid = os.fork()

    if pid == 0:
        print(f"  子行程: PID={os.getpid()}, 結束")
        sys.exit(42)  # 以 42 結束
    else:
        print(f"  父行程: 子行程 PID={pid} 已結束（未 wait）")
        print(f"  請開另一個終端執行 'ps aux | grep Z' 查看殭屍")
        time.sleep(8)  # 這時候子行程是殭屍
        _, status = os.wait()  # 現在才收集
        print(f"  父行程: wait 後, 子行程結束碼 = {os.WEXITSTATUS(status)}")


if __name__ == "__main__":
    demo_basic_fork()
    demo_fork_shared_vs_copy()

    print("=" * 50)
    print("執行 [孤兒行程] 範例…")
    if os.fork() == 0:
        demo_fork_orphan()
    else:
        os.wait()
