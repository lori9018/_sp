#!/usr/bin/env python3
"""
pipe_redirect.py - 示範 pipe + fork + dup2 + exec 的完整組合

模擬 shell 的管線 (pipe) 操作：
    ls -la | grep "\.py" | wc -l
"""

import os
import sys

def demo_pipe_basic():
    """基本 pipe: 父子行程透過管道通訊"""
    print("=" * 50)
    print("[pipe 基本] 父子行程透過管道通訊")

    r_fd, w_fd = os.pipe()  # r_fd 讀取端, w_fd 寫入端

    pid = os.fork()

    if pid == 0:
        # 子行程：關閉讀取端，寫入資料
        os.close(r_fd)
        os.write(w_fd, b"Hello from child!\n")
        os.write(w_fd, b"Message 2\n")
        os.write(w_fd, b"Message 3\n")
        os.close(w_fd)
        sys.exit(0)
    else:
        # 父行程：關閉寫入端，讀取資料
        os.close(w_fd)
        data = b""
        while True:
            chunk = os.read(r_fd, 1024)
            if not chunk:
                break
            data += chunk
        os.close(r_fd)
        os.wait()

        print(f"  父行程收到 ({len(data)} bytes):")
        print(f"  {data.decode()!r}")
    print()

def demo_pipe_ls_wc():
    """模擬 ls | wc -l"""
    print("=" * 50)
    print("[pipe 模擬] ls | wc -l")

    r_fd, w_fd = os.pipe()
    pid = os.fork()

    if pid == 0:
        # 子行程：ls -la，寫入管道
        os.close(r_fd)       # 不需要讀取端
        os.dup2(w_fd, 1)     # stdout → pipe 寫入端
        os.close(w_fd)
        os.execvp("ls", ["ls", "-la"])
        sys.exit(1)
    else:
        # 父行程：從管道讀取
        os.close(w_fd)
        data = b""
        while True:
            chunk = os.read(r_fd, 4096)
            if not chunk:
                break
            data += chunk
        os.close(r_fd)
        os.wait()

        # 計算行數
        lines = data.decode().strip().split("\n")
        print(f"  行數: {len(lines)}")
    print()

def demo_pipe_ls_grep_wc():
    """
    模擬 ls -la | grep "\.py" | wc -l
    需要兩個 pipe 與兩個子行程
    """
    print("=" * 50)
    print("[pipe 鏈] ls -la | grep '\\.py' | wc -l")

    # 第一個 pipe: ls → grep
    pipe1_r, pipe1_w = os.pipe()
    # 第二個 pipe: grep → wc
    pipe2_r, pipe2_w = os.pipe()

    # --- 建立 grep (中間行程) ---
    pid_grep = os.fork()

    if pid_grep == 0:
        # grep 子行程
        os.close(pipe1_w)   # 不寫入 pipe1
        os.close(pipe2_r)   # 不讀取 pipe2

        os.dup2(pipe1_r, 0)  # stdin ← pipe1 讀取端（來自 ls）
        os.dup2(pipe2_w, 1)  # stdout → pipe2 寫入端（前往 wc）

        os.close(pipe1_r)
        os.close(pipe2_w)

        os.execvp("grep", ["grep", "\\.py"])
        sys.exit(1)

    # --- 建立 wc (最後一個行程) ---
    pid_wc = os.fork()

    if pid_wc == 0:
        # wc 子行程
        os.close(pipe1_r)
        os.close(pipe1_w)
        os.close(pipe2_w)

        os.dup2(pipe2_r, 0)  # stdin ← pipe2 讀取端（來自 grep）

        os.close(pipe2_r)

        os.execvp("wc", ["wc", "-l"])
        sys.exit(1)

    # --- 父行程：執行 ls ---
    os.close(pipe1_r)
    os.close(pipe2_r)
    os.close(pipe2_w)

    os.dup2(pipe1_w, 1)  # stdout → pipe1 寫入端（前往 grep）
    os.close(pipe1_w)

    os.execvp("ls", ["ls", "-la"])
    # 父行程也被 exec 取代，不會到這裡

def demo_shell_pipeline():
    """用迴圈實作通用的管線執行器"""
    print("=" * 50)
    print("[通用管線] 執行任意指令鏈")

    commands = [
        ["ls", "-la"],
        ["grep", "\\.py"],
        ["wc", "-l"],
    ]

    def run_pipeline(cmd_list):
        """執行指令管線，回傳最後一個指令的輸出"""
        num_cmds = len(cmd_list)
        prev_r = None  # 上一個 pipe 的讀取端

        for i, cmd in enumerate(cmd_list):
            if i < num_cmds - 1:
                r_fd, w_fd = os.pipe()  # 建立 pipe
            else:
                r_fd, w_fd = None, None

            pid = os.fork()

            if pid == 0:
                # 子行程
                if prev_r is not None:
                    os.dup2(prev_r, 0)  # stdin ← 上個 pipe
                    os.close(prev_r)

                if i < num_cmds - 1:
                    os.close(r_fd)       # 不需要讀取端
                    os.dup2(w_fd, 1)     # stdout → pipe
                    os.close(w_fd)

                os.execvp(cmd[0], cmd)
                sys.exit(1)
            else:
                # 父行程
                if prev_r is not None:
                    os.close(prev_r)
                if i < num_cmds - 1:
                    os.close(w_fd)
                    prev_r = r_fd  # 傳遞給下一個指令
                else:
                    prev_r = None

                # 最後一個指令：讀取輸出
                if i == num_cmds - 1:
                    output = b""
                    buf = os.read(r_fd, 4096) if r_fd else b""
                    while buf:
                        output += buf
                        buf = os.read(r_fd, 4096)
                    os.close(r_fd)

                os.wait()  # 等待子行程結束

        return output

    output = run_pipeline(commands)
    print(f"  管線輸出: {output.decode().strip()}")
    print()


if __name__ == "__main__":
    demo_pipe_basic()
    demo_pipe_ls_wc()

    # demo_pipe_ls_grep_wc() 會 exec ls，取代主行程
    print("執行 [pipe 鏈] ls | grep .py | wc -l")
    pid = os.fork()
    if pid == 0:
        demo_pipe_ls_grep_wc()
    else:
        os.wait()
    print()

    demo_shell_pipeline()
