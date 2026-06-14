# 課程：系統程式 -- 筆記、習題與報告

欄位 | 內容
-----|--------
學期 | 114 學年下學期
學生 | 張庭亞
學號末兩碼 | 30
教師 | [陳鍾誠](https://www.nqu.edu.tw/educsie/index.php?act=blog&code=list&ids=4)
學校科系 | [金門大學資訊工程系](https://www.nqu.edu.tw/educsie/index.php)
課程教材 | https://github.com/ccc114b/cpu2os<br/>https://github.com/cccbook/ai-teach-you/blob/main/sp/tw/README.md<br/>https://github.com/ccc-c/c0computer

---
作業皆是用Gemini和opencode完成
無複製他人內容

## 📂 目錄結構

```
_SP/
├── README.md          ← 本文件（總整理）
├── HW1/  p0 語言編譯器 + VM（C 語言實作）
├── HW2/  HanScript 韓文關鍵字編譯器（Python 實作）
├── HW3/  貪食蛇遊戲（HTML + CSS + JS）
├── HW4/  系統程式概論電子書
├── HW5/  Thread / Race Condition / Mutex / Deadlock 文件
├── HW6/  行程與檔案系統程式設計（Python 實作）
└── MID/  inotify 檔案目錄監控工具（C 語言實作）
```

---

## HW1 — p0 語言編譯器與虛擬機

> `compiler.c` / `bnf.md` / `call.md` / `README.MD`

| 元件 | 說明 |
|------|------|
**詞法分析器 (Lexer)** | `next_token()` 辨識數字、識別字、關鍵字 (`func`, `if`, `return`, `while`) 與運算子，支援 `//` 與 `/* */` 註解 |
**語法分析器 (Parser)** | 遞迴下降 (Recursive Descent) 解析 Expression → Arith → Term → Factor 的運算子優先權 |
**中間碼 (IR)** | 產生四元組 (Quadruples)：`CALL`, `PARAM`, `FUNC_BEG`, `FUNC_END`, `FORMAL`, `RET_VAL`, `JMP_F`, `CMP_EQ` 等 |
**虛擬機 (VM)** | `stack[1000]` 堆疊框架模型 — 每次函式呼叫推入一個 Frame（含區域變數、返回位址、引數儲存區），支援遞迴 |
**p0 範例** | `fact.p0`（階乘遞迴）、`prime.p0`（質數檢測）、`while.p0`（1+…+10）、`if.p0`（條件分支） |

### 💡 關鍵觀念

- **堆疊框架 (Stack Frame)**：每個函式呼叫建立獨立 Frame，sp (Stack Pointer) 管理邊界，區域變數透過 `sp + offset` 存取
- **四元組 IR**：編譯器將 AST 線性化為 `op, arg1, arg2, result` 形式，VM 逐條執行
- **遞迴支援**：每次遞迴呼叫建立新的 Frame，`n` 存在各自的 Frame 內，互不干擾

---

## HW2 — HanScript 韓文關鍵字編譯器

> `hanscript.py` / `README.md`

| 元件 | 說明 |
|------|------|
**詞法分析器** | 正規表達式 `re.match()` 逐一匹配 token，韓文關鍵字如 `변수` (var)、`출력` (print)、`만약` (if)、`반복` (while) |
**語法分析器** | 遞迴下降建構 AST，節點類型：`ASSIGN_STMT`, `IF_STMT`, `WHILE_STMT`, `PRINT_STMT`, `BIN_OP`, `COMPARE` |
**路線 A：編譯器 + VM** | AST → Bytecode → 堆疊式 VM 執行。Bytecode 指令：`PUSH`, `LOAD`, `STORE`, `JUMP_IF_FALSE`, `ADD`, `SUB` 等 |
**路線 B：直譯器** | 直接走訪 AST 節點 (AST Walker)，使用 Python 原生 while 處理 `반복` |
**範例** | `circle.txt`（while 迴圈計算 5!）、`Four_arithmetic_operation.txt`（長方形面積） |

### 💡 關鍵觀念

- **雙重執行路線**：同一份 AST 可走編譯+VM 或純直譯，示範兩種實作策略
- **Bytecode 補丁 (Patch)**：while 迴圈在編譯時先填入暫存跳躍位址，結束後再回頭補上正確偏移
- **堆疊式 VM**：運算元堆疊 (Operand Stack) + 變數記憶體 (Memory)，指令從堆疊取出運算元、推回結果

---

## HW3 — 貪食蛇遊戲

> `snake.html` / `README.md`

純前端 HTML + CSS + JavaScript，單一檔案免安裝。

- **控制**：方向鍵移動、空白鍵/P 暫停
- **機制**：吃食物增長、撞牆/撞自己 Game Over
- **技術**：Canvas 繪圖、requestAnimationFrame 搭配 setInterval 遊戲迴圈、localStorage 儲存最高分

---

## HW4 — 系統程式概論電子書

> `系統程式概論.md`

19 章約 1.2 萬字的系統程式學習筆記：

| 章節 | 主題 |
|------|------|
1–3 | 系統程式定義、馮紐曼架構、CPU 指令週期、中斷、OS 核心/使用者模式 |
4–6 | 行程管理 (PCB、fork)、執行緒 (pthread)、CPU 排程 (FCFS、SJF、RR、MLFQ) |
7–8 | 記憶體管理 (分段/分頁、TLB)、虛擬記憶體 (Demand Paging、頁面置換) |
9–10 | 檔案系統 (inode、FAT/NTFS、VFS)、I/O 系統 (DMA、中斷驅動) |
11–13 | 系統呼叫流程、編譯器架構、ELF 格式、靜態/動態連結、載入器 |
14–16 | 號誌與同步、死結 (Coffman 4 條件、處理策略)、Socket 與 epoll |
17–19 | 安全 (Buffer Overflow、ASLR、Container)、效能分析 (perf/strace/gdb)、實作範例 |

---

## HW5 — Thread / Race Condition / Mutex / Deadlock

> `thread-race-mutex-deadlock.md`

| 主題 | 重點 |
|------|------|
**Thread** | 行程 vs 執行緒比較、`pthread_create/join`、使用者層級 vs 核心層級 (1:1 NPTL) |
**Race Condition** | 計數器交錯執行 (load/add/store)、TOCTOU 漏洞、延遲初始化問題 |
**Mutex** | 原子操作 (Test-and-Set / Compare-and-Swap)、Spinlock vs Mutex、遞迴鎖、RAII 管理 |
**Deadlock** | Coffman 4 條件、Lock Ordering、trylock、銀行家演算法、Ostrich Algorithm |

### 💡 關鍵觀念

- Race → Mutex → Deadlock 是一條因果鏈：多 Thread 共用資源 → Race Condition → Mutex 保護 → 不當使用 → Deadlock
- 預防 Deadlock 最務實的手段：**統一的 Lock Ordering**

---

## HW6 — 行程與檔案系統程式設計

> `fork.py` / `execvp.py` / `file_ops.py` / `dup2.py` / `pipe_redirect.py` / `main.py` / `README.md`

使用 Python `os` 模組封裝 Unix 系統呼叫的實作練習：

| 範例 | API 重點 |
|------|---------|
**fork.py** | `os.fork()` — 行程複製、寫入時複製 (CoW)、孤兒/殭屍行程 |
**execvp.py** | `os.execvp()` — 行程映像替換、`fork + exec + wait` 經典組合 |
**file_ops.py** | `os.open/close/read/write/lseek` — 低階檔案操作、fd 編號 (0/1/2) |
**dup2.py** | `os.dup2()` — stdin/stdout/stderr 重新導向、模擬 shell `>` |
**pipe_redirect.py** | `os.pipe()` + fork + dup2 + exec — 管線 `ls \| grep \| wc` |

### 💡 關鍵觀念

- **fork + exec + wait**：行程建立的標準三部曲
- **fd 0=stdin, 1=stdout, 2=stderr**：Unix 一切皆檔案，重新導向就是 dup2 改變 fd 指向
- **Pipe**：讀取端與寫入端兩端的 fd，搭配 dup2 串接多行程形成管線

---

## MID — inotify 檔案目錄監控工具

> `watcher.c` / `README.md`

C 語言實作、使用 Linux 核心 inotify 機制的檔案監控工具。

| 項目 | 說明 |
|------|------|
**初始化** | `inotify_init()` 建立 inotify 實例回傳 fd |
**註冊監控** | `inotify_add_watch(fd, path, IN_CREATE\|IN_MODIFY\|IN_DELETE)` |
**事件讀取** | `read(fd, buf, size)` — **阻塞式讀取**，無事件時行程睡眠 |
**信號處理** | `sigaction(SIGINT, handler)` 優雅關閉 fd，避免資源洩漏 |

### 💡 關鍵觀念

- **事件驅動 vs 輪詢**：inotify 是核心主動通知，無需 sleep + scan
- **Blocking Read**：`read()` 在無事件時阻塞、讓出 CPU，有事件時核心喚醒
- **Bitmask**：`event->mask` 以位元遮罩同時表達多種事件屬性（如 `IN_CREATE | IN_ISDIR`）

---

## 🧠 總複習：系統程式學習路徑

```
                         ┌── 編譯器 (HW1 C / HW2 Python)
                         │      Lexer → Parser → IR/Bytecode → VM
                         │
數字電路 / 組合語言 ──→  作業系統 ──→  系統程式
                         │               │
                         │               ├── 行程管理 (fork/exec)     ── HW6
                         │               ├── 記憶體管理 (虛擬記憶體)   ── HW4
                         │               ├── 檔案系統 (open/read/fd)  ── HW6
                         │               ├── 同步 (Mutex/Deadlock)   ── HW5
                         │               └── 監控 (inotify)          ── MID
                         │
                         └── 應用程式
                                Snake Game (HW3)
```

---

*最後更新：2026-06-14*
