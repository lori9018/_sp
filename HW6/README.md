# HW6 — 行程與檔案系統程式設計 (Process & File System Programming)

本專案使用 Python 搭配 `os` 模組，示範 Unix 系統程式設計的核心 API，包含行程管理、檔案操作、重新導向與管線通訊。

---

## 📂 檔案列表

| 檔案 | 主題 | 示範內容 |
|------|------|---------|
| `fork.py` | 行程建立 | `os.fork()`、寫入時複製、孤兒行程、殭屍行程 |
| `execvp.py` | 行程替換 | `os.execvp()`、`fork + exec` 經典模式、錯誤處理 |
| `file_ops.py` | 檔案操作 | `os.open/close/read/write`、`os.lseek`、fd 編號 |
| `dup2.py` | 重新導向 | `os.dup2()`、stdin/stdout/stderr 重新導向、shell `>` 模擬 |
| `pipe_redirect.py` | 管線通訊 | `os.pipe()`、`ls \| wc -l`、`ls \| grep \| wc` 多階段管線 |
| `main.py` | 總入口 | 互動選單統一執行各範例 |

---

## 🧠 核心概念

### 行程管理 (Process)

| API | 說明 |
|-----|------|
| `os.fork()` | 複製目前行程，回傳 0 給子行程，子行程 PID 給父行程 |
| `os.execvp(file, args)` | 將目前行程替換為新的程式（`args[0]` 為程式名稱） |
| `os.wait()` | 等待子行程結束，收集其終止狀態 |
| `os.getpid()` | 取得目前行程 PID |
| `os.getppid()` | 取得父行程 PID |

**經典組合：`fork + exec + wait`**

```
父行程 ──fork()──→ 子行程
    │                  │
    │                  ├── execvp() → 變成新程式
    │                  │
    └── wait() ←────────┘ 等待結束
```

---

### 檔案描述子 (File Descriptor)

在 Unix 系統中，每個行程都有 3 個標準檔案描述子：

| FD | 名稱 | 對應裝置 |
|----|------|---------|
| **0** | stdin (標準輸入) | 鍵盤 |
| **1** | stdout (標準輸出) | 螢幕 |
| **2** | stderr (標準錯誤) | 螢幕 |

新開啟的檔案會從 `3` 開始分配，關閉的 fd 會被復用。

---

### 低階檔案操作

| API | 對應系統呼叫 | 功能 |
|-----|------------|------|
| `os.open(path, flags, mode)` | `open()` | 開啟檔案，回傳 fd |
| `os.read(fd, n)` | `read()` | 從 fd 讀取 n bytes |
| `os.write(fd, data)` | `write()` | 將 bytes 寫入 fd |
| `os.close(fd)` | `close()` | 關閉檔案 |
| `os.lseek(fd, offset, whence)` | `lseek()` | 移動檔案讀寫指標 |

**旗標 (flags)**：

| 旗標 | 說明 |
|------|------|
| `os.O_RDONLY` | 唯讀 |
| `os.O_WRONLY` | 唯寫 |
| `os.O_RDWR` | 讀寫 |
| `os.O_CREAT` | 不存在則建立 |
| `os.O_TRUNC` | 存在則清空 |
| `os.O_APPEND` | 附加模式 |

---

### 重新導向 (dup2)

```python
os.dup2(old_fd, new_fd)
```

將 `new_fd` 複製為 `old_fd` 的副本（自動關閉 `new_fd` 原本的指向）。

**典型應用**：

```
# stdout → 檔案
fd = os.open("output.txt", os.O_WRONLY | os.O_CREAT)
os.dup2(fd, 1)   # 現在 fd 1 指向檔案
print("寫入檔案")  # 輸出會進到檔案
```

---

### 管線 (Pipe)

```python
r_fd, w_fd = os.pipe()
# r_fd: 讀取端, w_fd: 寫入端
```

**管線模擬 `ls | wc -l`**：

```
ls (子行程)       pipe        wc (父行程)
stdout ──────► r_fd ──► stdin
              w_fd
```

- 子行程：`dup2(w_fd, 1)` + `execvp("ls")` → ls 輸出寫入 pipe
- 父行程：從 `r_fd` 讀取資料 → 傳給 `wc`

---

## ▶️ 如何使用

```bash
# 直接執行單一範例
python fork.py
python execvp.py
python file_ops.py
python dup2.py
python pipe_redirect.py

# 或使用互動總入口
python main.py
```

> ⚠️ 注意：`execvp.py` 中的某些範例（如 `demo_execvp_ls()`）會直接取代當前行程，建議從 `main.py` 執行或手動確認。

---

## 🔗 參考

- [Python os 模組文件](https://docs.python.org/3/library/os.html)
- [Unix man pages (section 2) — syscalls](https://man7.org/linux/man-pages/man2/syscalls.2.html)
- Operating Systems: Three Easy Pieces
- Advanced Programming in the UNIX Environment (Stevens)
