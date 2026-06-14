/*
 * watcher.c — 簡易檔案目錄監控工具 (File Watcher)
 *
 * 使用 Linux inotify 機制監控指定目錄的檔案異動事件。
 * 監聽事件：建立 (IN_CREATE)、修改 (IN_MODIFY)、刪除 (IN_DELETE)。
 *
 * 編譯：gcc -o watcher watcher.c
 * 使用：./watcher /path/to/watch
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

/*
 * <sys/inotify.h>：提供 inotify_init()、inotify_add_watch()、
 * inotify_rm_watch() 及 struct inotify_event 等類型與函式。
 */
#include <sys/inotify.h>

/*
 * <errno.h>：提供 errno 全局變數，系統呼叫失敗時會設定 errno
 * 用以指示具體的錯誤原因。
 */
#include <errno.h>

/*
 * <sys/types.h>：定義一些系統層級的資料類型，如 mode_t、ssize_t 等。
 * 某些系統中 inotify 相關結構可能會依賴此標頭。
 */
#include <sys/types.h>

/*
 * <linux/limits.h>：定義路徑相關的常數，如 PATH_MAX（4096）。
 */
#include <linux/limits.h>

/* ─── 全域變數 ─── */

/* inotify 的檔案描述子，儲存在全域變數中以便 signal handler 能存取 */
static int inotify_fd = -1;

/* 被監控的目錄路徑（僅供顯示用） */
static const char *watch_path = NULL;

/* ─── SIGINT 處理常式 ─── */

/*
 * handle_signal — SIGINT (Ctrl+C) 的處理函式。
 *
 * 當使用者按下 Ctrl+C 時，核心會送出 SIGINT 信號給行程。
 * 此函式負責優雅地關閉 inotify 檔案描述子後結束程式，
 * 避免 fd 洩漏。
 */
static void handle_signal(int sig)
{
    (void)sig; /* 明確標示未使用的參數，避免編譯器警告 */

    fprintf(stdout, "\n[INFO] 收到 SIGINT，正在關閉監控…\n");

    if (inotify_fd != -1) {
        /*
         * close(inotify_fd)：
         *   關閉 inotify 檔案描述子，釋放核心中的 inotify 實例，
         *   所有透過此 inotify_fd 註冊的 watch 都會被自動移除。
         */
        close(inotify_fd);
        inotify_fd = -1;
    }

    /*
     * _exit(0) 而非 exit(0)：
     *   exit() 會執行 atexit 註冊的函式並清理 stdio 緩衝區；
     *   _exit() 則直接進入核心進行行程終止，在 signal handler 中
     *   使用更安全，可避免在 handler 中執行複雜的清理動作造成死結。
     */
    _exit(0);
}

/* ─── 設定 signal handler ─── */

/*
 * setup_signal_handler — 註冊 SIGINT 的處理函式。
 *
 * signal(SIGINT, handle_signal)：
 *   告知核心，當此行程收到 SIGINT 信號時，由 handle_signal 來處理，
 *   而非使用預設行為（終止行程）。這讓我們有機會在結束前釋放資源。
 */
static void setup_signal_handler(void)
{
    struct sigaction sa;

    /*
     * sigaction 比 signal() 更可靠、可攜性更高。
     * memset 先將結構清零，避免未初始化欄位造成非預期行為。
     */
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_signal;          /* 指定處理函式 */

    /*
     * sigemptyset(&sa.sa_mask)：
     *   設定在 handler 執行期間要「屏蔽」的信號集合。
     *   這裡設為空集合，表示不屏蔽任何信號。
     */
    sigemptyset(&sa.sa_mask);

    /*
     * sa_flags = 0：
     *   使用預設行為。不設定 SA_RESTART，這樣被信號中斷的系統呼叫
     *   （如 read）會回傳 -1 並設定 errno = EINTR，讓主迴圈可以
     *   自然退出。
     */
    sa.sa_flags = 0;

    if (sigaction(SIGINT, &sa, NULL) < 0) {
        /*
         * sigaction 失敗的可能性很低，但若發生（例如無效的 sa 指標），
         * 使用 perror 印出錯誤訊息再終止程式。
         */
        perror("[ERROR] sigaction 設定失敗");
        exit(EXIT_FAILURE);
    }
}

/* ─── 印出事件名稱（輔助函式） ─── */

/*
 * event_name — 根據 inotify_event 的 mask 回傳中文事件名稱。
 *
 * inotify_event.mask 是一個位元遮罩（bitmask），同一事件可能同時
 * 觸發多個旗標（例如 IN_CREATE | IN_ISDIR 表示建立的是目錄），
 * 因此我們使用 if 逐一比對而非 switch。
 */
static const char *event_name(uint32_t mask)
{
    if (mask & IN_CREATE)
        return "建立 (CREATE)";
    if (mask & IN_MODIFY)
        return "修改 (MODIFY)";
    if (mask & IN_DELETE)
        return "刪除 (DELETE)";
    return "其他 (OTHER)";
}

/* ─── 主程式 ─── */

int main(int argc, char *argv[])
{
    /*
     * inotify_event 結構由核心填入，每次 read() 回傳的緩衝區中可能
     * 包含一個或多個 inotify_event 結構，因此我們需要一個足夠大的緩衝區
     * （通常使用 sizeof(struct inotify_event) + PATH_MAX + 16 來確保可容納
     * 最長的檔名）。
     */
    char buf[sizeof(struct inotify_event) + PATH_MAX + 16]
        __attribute__((aligned(__alignof__(struct inotify_event))));

    int wd;               /* watch descriptor，註冊監控後核心回傳的辨識碼 */
    ssize_t num_read;     /* read() 回傳的實際讀取位元組數 */
    struct inotify_event *event; /* 指向緩衝區中目前正在處理的事件 */

    /* ─── 檢查命令列參數 ─── */

    /*
     * 程式需要一個命令列參數：要監控的目錄路徑。
     * 若未提供，則印出使用說明並結束程式。
     */
    if (argc < 2) {
        fprintf(stderr, "使用方法: %s <監控目錄路徑>\n", argv[0]);
        fprintf(stderr, "範例:     %s /tmp/myfolder\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    watch_path = argv[1];
    fprintf(stdout, "[INFO] 目標目錄: %s\n", watch_path);

    /* ─── 註冊 SIGINT 信號處理 ─── */
    setup_signal_handler();

    /* ─── 初始化 inotify 實例 ─── */

    /*
     * inotify_init()：
     *   建立一個 inotify 實例，回傳一個檔案描述子。
     *   這個 fd 後續會用來新增監控目標以及讀取事件。
     *   回傳 -1 表示失敗（例如系統已達 inotify 實例上限）。
     */
    inotify_fd = inotify_init();
    if (inotify_fd < 0) {
        perror("[ERROR] inotify_init 失敗");
        exit(EXIT_FAILURE);
    }

    fprintf(stdout, "[INFO] inotify fd: %d\n", inotify_fd);

    /* ─── 新增監控目標 ─── */

    /*
     * inotify_add_watch(fd, path, mask)：
     *   向 inotify 實例 (fd) 註冊對 path 目錄的監控。
     *   mask = IN_CREATE | IN_MODIFY | IN_DELETE，表示我們只關心
     *   這三種事件。回傳值是 watch descriptor (wd)，可用於後續移除監控。
     *
     *   參數 path 必須是一個已存在的目錄，否則回傳 -1。
     */
    wd = inotify_add_watch(inotify_fd, watch_path,
                           IN_CREATE | IN_MODIFY | IN_DELETE);
    if (wd < 0) {
        /*
         * 常見失敗原因：路徑不存在、權限不足、或 inotify watch 已達上限
         * （可透過 /proc/sys/fs/inotify/max_user_watches 調整）。
         */
        perror("[ERROR] inotify_add_watch 失敗");
        close(inotify_fd);
        exit(EXIT_FAILURE);
    }

    fprintf(stdout, "[INFO] 開始監聽目錄: %s\n", watch_path);
    fprintf(stdout, "      監聽事件: 建立 | 修改 | 刪除\n");
    fprintf(stdout, "      按下 Ctrl+C 結束程式\n\n");

    /* ─── 事件處理主迴圈 ─── */

    while (1) {
        /*
         * read(inotify_fd, buf, sizeof(buf))：
         *   這是整個程式的核心——「阻塞式讀取（Blocking Read）」。
         *
         *   當 inotify fd 上沒有任何待處理的事件時，read() 會「阻塞」
         *   （Block），亦即讓出 CPU，行程進入睡眠狀態，直到核心在該
         *   目錄上偵測到檔案異動，將事件資料寫入 inotify 佇列，並喚醒
         *   此行程後，read() 才會回傳。
         *
         *   這種設計完全不需要輪詢（Polling），CPU 使用率極低，是事件
         *   驅動（Event-Driven）架構的典型範例。
         *
         *   回傳值 num_read 表示實際讀取的位元組數；-1 表示發生錯誤；
         *   0 則不應發生（inotify fd 沒有 EOF 的概念）。
         */
        num_read = read(inotify_fd, buf, sizeof(buf));
        if (num_read < 0) {
            /*
             * EINTR：read 被信號中斷。
             *   當我們按 Ctrl+C 時，handle_signal 被執行並呼叫 _exit(0)，
             *   理論上不會走到這裡。但若在其他場景收到 SIGINT（例如
             *   信號送到行程群組），read 可能因被中斷而回傳 -1 且
             *   errno == EINTR。此時我們繼續等待即可。
             */
            if (errno == EINTR) {
                continue;
            }
            /*
             * 其他 read 錯誤（機率極低），印出錯誤訊息並結束。
             */
            perror("[ERROR] read 失敗");
            break;
        }

        /*
         * 逐筆處理緩衝區中的事件。
         *
         * 核心可能一次回傳多筆事件（例如大量檔案同時被建立），
         * 因此我們需要透過 event->len 來計算下一筆事件的偏移量。
         *
         * 指標運算：從 buf 的開頭開始，依序處理每個 inotify_event，
         *           然後將指標前進 sizeof(struct inotify_event) + event->len。
         */
        for (char *ptr = buf; ptr < buf + num_read;
             ptr += sizeof(struct inotify_event) + event->len) {

            /*
             * 將目前位置的 char* 強制轉型為 struct inotify_event*，
             * 這樣就能透過 event->mask、event->name 等欄位讀取事件資訊。
             */
            event = (struct inotify_event *)ptr;

            /*
             * event->len 表示檔名字串的長度（包含結尾的 '\0'）。
             * 以下兩種情況不會有檔名：
             *   1) event->len == 0（核心沒有提供檔名）
             *   2) event->mask & IN_IGNORED（watch 被核心移除）
             */
            if (event->len > 0 && !(event->mask & IN_IGNORED)) {
                /*
                 * event->name 是可變長度陣列（flexible array member），
                 * 儲存發生事件之檔案的名稱。
                 *
                 * event->mask 是位元遮罩，表示發生的事件類型。
                 * 我們使用 event_name() 將其轉換為可讀文字。
                 */
                fprintf(stdout, "[%s] 檔案: %s\n",
                        event_name(event->mask), event->name);

                /*
                 * event->mask & IN_ISDIR：
                 *   若此位元被設定，表示事件發生在「目錄」上而非一般檔案。
                 *   我們僅用括弧標示以供參考，不特別處理。
                 */
                if (event->mask & IN_ISDIR) {
                    fprintf(stdout, "       → (此為目錄)\n");
                }
            }
        }

        /*
         * 每次處理完一批事件後強制刷新 stdout 緩衝區，
         * 確保輸出即時顯示在使用者終端上（因為 stdout 預設
         * 是行緩衝，若輸出沒有換行可能不會立即顯示）。
         */
        fflush(stdout);
    }

    /* ─── 清理資源（正常情況下由 SIGINT 處理，此處為防禦性寫法） ─── */

    if (inotify_fd != -1) {
        close(inotify_fd);
    }

    return 0;
}
