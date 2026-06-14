# 簡易檔案目錄監控工具 (File Watcher)

使用 Linux `inotify` 機制監控指定目錄的檔案異動事件。

## 需求

- Linux 作業系統（核心 2.6.13 以上）
- `gcc` 編譯器

## 編譯與執行

```bash
# 編譯
gcc -o watcher watcher.c

# 執行（監控 /tmp/testdir）
./watcher /tmp/testdir

# 在另一個終端測試
touch /tmp/testdir/hello.txt
echo "hi" > /tmp/testdir/hello.txt
rm /tmp/testdir/hello.txt
```

按下 `Ctrl+C` 結束程式。

## 執行流程

```
main()
  │
  ├── 檢查命令列參數（argv[1] 必須存在）
  │
  ├── setup_signal_handler()
  │     └── sigaction(SIGINT, handle_signal)
  │
  ├── inotify_init()          ← 建立 inotify 實例，取得 fd
  │
  ├── inotify_add_watch(      ← 註冊監控：目錄 + 事件遮罩
  │     fd, path,
  │     IN_CREATE|IN_MODIFY|IN_DELETE)
  │
  └── while (1)  事件處理主迴圈
        │
        ├── read(fd, buf, size)  ← 阻塞等待事件發生
        │     │
        │     ├── 有事件 → 回傳資料
        │     └── EINTR  → continue（被信號中斷）
        │
        └── 逐筆解析 inotify_event
              ├── event->mask  → 事件類型（建立/修改/刪除）
              ├── event->name  → 檔名
              └── 印出到 stdout

Ctrl+C → handle_signal()
          ├── close(inotify_fd)
          └── _exit(0)
```

## 核心觀念

### 1. 事件驅動 vs 輪詢

傳統作法需要每 N 秒掃描一次目錄（Polling），浪費 CPU 且即時性差。`inotify` 是 **事件驅動** 機制：核心在檔案異動發生時主動產生事件，行程透過 `read()` 阻塞等待，CPU 使用率趨近於零。

### 2. 阻塞式讀取 (Blocking Read)

```c
num_read = read(inotify_fd, buf, sizeof(buf));
```

`inotify_fd` 的行為類似一般檔案的讀取，但其特殊之處在於：
- 沒有事件時：`read()` **阻塞**，行程進入睡眠（TASK_INTERRUPTIBLE），被核心移出排程佇列
- 有事件時：核心將事件寫入內部佇列，喚醒行程，`read()` 回傳
- 完全不需要 `while(1) { sleep(1); check(); }` 這類輪詢

### 3. 檔案描述子 (File Descriptor) 抽象

`inotify_init()` 回傳的是一個 **fd**，這讓 inotify 可以與 `select()`、`poll()`、`epoll()` 等 I/O 多工機制整合，實現同時監控多個 fd 的進階應用。

### 4. 信號處理與資源釋放

`SIGINT` 處理常式負責 `close(inotify_fd)`，因為 fd 是核心資源，行程結束後若未關閉會造成 fd 洩漏（雖然行程結束時核心會自動回收，但明確關閉是良好的系統程式習慣）。使用 `_exit()` 而非 `exit()` 可避免在 signal handler 中執行複雜的 stdio 清理。

### 5. 位元遮罩事件類型

`event->mask` 使用 **位元遮罩 (Bitmask)** 表示事件類型：

```c
if (mask & IN_CREATE) { /* 建立事件 */ }
if (mask & IN_MODIFY) { /* 修改事件 */ }
if (mask & IN_DELETE) { /* 刪除事件 */ }
if (mask & IN_ISDIR)  { /* 發生在目錄上 */ }
```

同一事件可能同時設置多個位元（例如 `IN_CREATE | IN_ISDIR` 表示建立了一個子目錄），因此使用 `&` 逐一比對而非 `switch`。

## 可擴充方向

- 使用 `epoll` 同時監控多個目錄
- 事件發生時記錄時間戳與完整路徑
- 支援 `IN_MOVED_FROM` / `IN_MOVED_TO`（移動事件）
- 改為守護行程 (Daemon) 背景執行
