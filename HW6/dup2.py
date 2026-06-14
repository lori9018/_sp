#!/usr/bin/env python3
"""
dup2.py - 示範 os.dup2() 與檔案描述子重新導向

dup2(old_fd, new_fd) 將 new_fd 複製為 old_fd 的副本，
關閉 new_fd 原本指向的檔案（如有），
之後 new_fd 和 old_fd 指向同一個開啟檔案。

常用於：重新導向 stdin(0), stdout(1), stderr(2)
"""

import os
import sys

def demo_dup2_basic():
    """dup2 基本操作：複製檔案描述子"""
    print("=" * 50)
    print("[dup2 基本操作]")

    # 開啟一個檔案，取得 fd = 3（或以上）
    fd = os.open("_demo_dup.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    print(f"  原始 fd: {fd}")

    # 用 dup2 將 fd 4 也指向同一個檔案
    # dup2(fd, 4) → fd 4 現在和 fd 指向同一開啟的檔案
    os.dup2(fd, 4)
    print(f"  dup2({fd}, 4): fd 4 現在指向同一個檔案")

    # 透過 fd 4 寫入
    os.write(4, b"Written via fd 4\n")
    # 透過原始 fd 寫入（會接在後面）
    os.write(fd, b"Written via original fd\n")

    os.close(fd)
    os.close(4)
    print()

def demo_stdout_redirect_to_file():
    """將 stdout (fd=1) 重新導向到檔案"""
    print("=" * 50)
    print("[stdout 重新導向]")


    fd = os.open("_demo_stdout.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    saved_fd = os.dup(1)  # 先備份原本的 stdout

    # dup2(fd, 1): 關閉 fd 1，讓它指向 fd 的檔案
    os.dup2(fd, 1)

    # 現在所有 print 輸出都會進到檔案
    print("這行會寫入檔案 1")
    print("這行也會寫入檔案 2")
    print("PID =", os.getpid())

    # 復原 stdout
    os.dup2(saved_fd, 1)
    os.close(fd)
    os.close(saved_fd)

    # 檢查檔案內容
    with open("_demo_stdout.txt") as f:
        content = f.read()
    print(f"  檔案內容 ({len(content)} chars):")
    print(f"  {content!r}")
    print()

def demo_stderr_redirect():
    """將 stderr (fd=2) 重新導向到檔案"""
    print("=" * 50)
    print("[stderr 重新導向]")

    fd = os.open("_demo_stderr.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    saved_fd = os.dup(2)

    os.dup2(fd, 2)

    # 這些錯誤訊息會進到檔案
    os.write(2, b"[stderr] 這個錯誤訊息寫入檔案\n")
    os.write(2, b"[stderr] 另一個錯誤\n")

    os.dup2(saved_fd, 2)
    os.close(fd)
    os.close(saved_fd)

    with open("_demo_stderr.txt") as f:
        print(f"  stderr 重導向內容: {f.read()!r}")
    print()

def demo_stdin_redirect_from_file():
    """將 stdin (fd=0) 重新導向從檔案讀取"""
    print("=" * 50)
    print("[stdin 重新導向]")

    # 建立一個輸入檔案
    with open("_demo_stdin.txt", "w") as f:
        f.write("Hello from file\n這是從檔案讀入的\nline 3\n")

    fd = os.open("_demo_stdin.txt", os.O_RDONLY)
    saved_fd = os.dup(0)

    os.dup2(fd, 0)

    # 現在 input() 會從檔案讀取
    line1 = input().strip()
    line2 = input().strip()
    line3 = input().strip()

    # 復原 stdin
    os.dup2(saved_fd, 0)
    os.close(fd)
    os.close(saved_fd)

    print(f"  stdin 重新導向讀取：")
    print(f"    line1: {line1}")
    print(f"    line2: {line2}")
    print(f"    line3: {line3}")
    print()

def demo_shell_redirect_simulation():
    """模擬 shell 的 > 重新導向 (fork + dup2 + exec)"""
    print("=" * 50)
    print("[shell 重新導向模擬] 將 echo 輸出寫入檔案")

    pid = os.fork()

    if pid == 0:
        # 子行程：將 stdout 重新導向到檔案，然後執行 echo
        fd = os.open("_demo_shell_redirect.txt",
                      os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        os.dup2(fd, 1)  # stdout → 檔案
        os.close(fd)

        os.execvp("echo", ["echo", "Hello from redirected shell!"])
        sys.exit(1)
    else:
        os.wait()
        with open("_demo_shell_redirect.txt") as f:
            print(f"  檔案內容: {f.read()!r}")
    print()

def demo_dup2_replaces_fd():
    """dup2 會自動關閉目標 fd"""
    print("=" * 50)
    print("[dup2 取代 fd 行為]")

    f1 = os.open("_demo_f1.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    f2 = os.open("_demo_f2.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

    print(f"  fd {f1} → _demo_f1.txt")
    print(f"  fd {f2} → _demo_f2.txt")

    # dup2(f1, f2) 會先關閉 f2，然後 f2 變成 f1 的副本
    os.dup2(f1, f2)

    # 現在寫入 f2 實際是寫到 _demo_f1.txt
    os.write(f2, b"This goes to f1 file via dup2!\n")

    os.close(f1)
    os.close(f2)

    with open("_demo_f1.txt") as f:
        print(f"  _demo_f1.txt: {f.read()!r}")
    with open("_demo_f2.txt") as f:
        print(f"  _demo_f2.txt: {f.read()!r}")
    print()


def cleanup():
    import glob
    for f in glob.glob("_demo_*.txt"):
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    cleanup()

    demo_dup2_basic()
    demo_stdout_redirect_to_file()
    demo_stderr_redirect()
    demo_stdin_redirect_from_file()
    demo_shell_redirect_simulation()
    demo_dup2_replaces_fd()

    cleanup()
