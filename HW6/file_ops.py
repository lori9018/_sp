#!/usr/bin/env python3
"""
file_ops.py - 示範低階檔案操作：open, close, read, write

使用 os.open(), os.close(), os.read(), os.write()
這些是 Unix 系統呼叫的直接封裝，不同於 Python 的 open()。
"""

import os
import sys

def demo_lowlevel_write():
    """使用 os.write() 直接寫入 stdout (fd=1)"""
    print("=" * 50)
    print("[os.write] 使用低階 write 系統呼叫")

    msg = b"  Hello from os.write() (fd=1)\n"
    os.write(sys.stdout.fileno(), msg)

    # fd 1 是 stdout
    msg2 = "  也可以直接寫到 fd 1\n".encode()
    os.write(1, msg2)
    print()

def demo_lowlevel_read():
    """使用 os.read() 從 stdin 讀取"""
    print("=" * 50)
    print("[os.read] 使用低階 read 系統呼叫")
    print("  請輸入一行文字：", end="")
    sys.stdout.flush()

    data = os.read(sys.stdin.fileno(), 100)  # 最多讀 100 bytes
    print(f"  讀取到 {len(data)} bytes: {data!r}")
    print()

def demo_open_write_close():
    """建立並寫入檔案"""
    print("=" * 50)
    print("[open/write/close] 建立檔案並寫入內容")

    filename = "_demo_lowlevel.txt"

    # os.O_WRONLY: 只寫模式
    # os.O_CREAT: 建立新檔案
    # os.O_TRUNC: 若存在則清空
    # 0644: 檔案權限 (rw-r--r--)
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    print(f"  → 檔案開啟: fd = {fd}")

    lines = [
        b"Low-level file operations\n",
        b"=======================\n",
        b"os.open() / os.read() / os.write() / os.close()\n",
        f"PID = {os.getpid()}\n".encode(),
    ]

    for line in lines:
        n = os.write(fd, line)
        print(f"  → 寫入 {n} bytes")

    os.close(fd)
    print(f"  → 檔案已關閉\n")

def demo_open_read_close():
    """讀取剛才建立的檔案"""
    print("=" * 50)
    print("[open/read/close] 讀取檔案內容")

    filename = "_demo_lowlevel.txt"

    fd = os.open(filename, os.O_RDONLY)
    print(f"  → 檔案開啟: fd = {fd}")

    content = b""
    while True:
        chunk = os.read(fd, 32)  # 一次讀 32 bytes
        if not chunk:            # EOF
            break
        content += chunk
        print(f"  → 讀取 {len(chunk)} bytes: {chunk!r}")

    os.close(fd)
    print(f"\n  → 完整內容 ({len(content)} bytes):")
    print(f"  {content.decode()!r}")
    print()

def demo_file_descriptor_numbers():
    """觀察檔案描述子編號"""
    print("=" * 50)
    print("[檔案描述子編號]")

    std_fds = [
        ("stdin  (fd 0)", sys.stdin.fileno()),
        ("stdout (fd 1)", sys.stdout.fileno()),
        ("stderr (fd 2)", sys.stderr.fileno()),
    ]
    for name, fd in std_fds:
        print(f"  {name}")

    # 開啟新檔案觀察 fd 編號
    fd1 = os.open("_demo_lowlevel.txt", os.O_RDONLY)
    print(f"  第一次開啟: fd = {fd1}")  # 通常是 3
    fd2 = os.open("_demo_lowlevel.txt", os.O_RDONLY)
    print(f"  第二次開啟: fd = {fd2}")  # 通常是 4
    os.close(fd1)
    fd3 = os.open("_demo_lowlevel.txt", os.O_RDONLY)
    print(f"  關閉 fd {fd1} 後再開啟: fd = {fd3}")  # 會復用 3

    os.close(fd2)
    os.close(fd3)
    print()

def demo_lseek():
    """使用 os.lseek() 在檔案中隨機讀寫"""
    print("=" * 50)
    print("[os.lseek] 在檔案中隨機存取")

    filename = "_demo_seek.txt"
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    os.write(fd, b"0123456789ABCDEFGHIJ")
    os.close(fd)

    fd = os.open(filename, os.O_RDONLY)

    # 跳到位置 5
    os.lseek(fd, 5, os.SEEK_SET)
    data = os.read(fd, 5)
    print(f"  lseek 到 5 後讀取 5 bytes: {data!r}")  # b'56789'

    # 從當前位置往後跳 3
    os.lseek(fd, 3, os.SEEK_CUR)
    data = os.read(fd, 5)
    print(f"  再跳 3 後讀取 5 bytes: {data!r}")  # b'HIJ' + ...

    # 跳到從結尾算起 -5
    os.lseek(fd, -5, os.SEEK_END)
    data = os.read(fd, 5)
    print(f"  lseek 到結尾 -5 後讀取 5 bytes: {data!r}")  # b'FGHIJ'

    os.close(fd)
    os.unlink(filename)  # 刪除暫存檔
    print()

def demo_error_handling():
    """檔案操作錯誤處理"""
    print("=" * 50)
    print("[錯誤處理]")

    # 開啟不存在的檔案
    try:
        os.open("/tmp/nonexistent_file_xyz123", os.O_RDONLY)
    except FileNotFoundError as e:
        print(f"  FileNotFoundError: {e}")

    # 唯讀檔案寫入
    try:
        fd = os.open("_demo_lowlevel.txt", os.O_RDONLY)
        os.write(fd, b"try write")
        os.close(fd)
    except OSError as e:
        print(f"  OSError: {e}")
        os.close(fd)


def cleanup():
    try:
        os.unlink("_demo_lowlevel.txt")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    cleanup()

    demo_lowlevel_write()
    demo_lowlevel_read()
    demo_open_write_close()
    demo_open_read_close()
    demo_file_descriptor_numbers()
    demo_lseek()
    demo_error_handling()

    cleanup()
