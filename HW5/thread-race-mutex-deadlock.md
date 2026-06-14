# Thread、Race Condition、Mutex、Deadlock 深入探討

## 目錄

1. [Thread（執行緒）](#1-thread執行緒)
2. [Race Condition（競爭條件）](#2-race-condition競爭條件)
3. [Mutex（互斥鎖）](#3-mutex互斥鎖)
4. [Deadlock（死結）](#4-deadlock死結)
5. [總結與對照](#5-總結與對照)

---

## 1. Thread（執行緒）

### 1.1 什麼是 Thread？

**Thread（執行緒）** 是 CPU 排程的最小單位，是行程（Process）內部的一條執行路徑。一個行程內可以包含多個執行緒，這些執行緒**共享同一個位址空間**（程式碼、資料、堆積），但各自擁有獨立的**堆疊**與**暫存器狀態**。

```
┌───────────── Process ─────────────┐
│                                    │
│  ┌───────┐  ┌───────┐  ┌───────┐ │
│  │Thread1│  │Thread2│  │Thread3│ │
│  │ Stack │  │ Stack │  │ Stack │ │
│  └───────┘  └───────┘  └───────┘ │
│                                    │
│  共用：Code / Data / Heap / FD     │
└────────────────────────────────────┘
```

### 1.2 Thread 與 Process 的比較

| 比較項目 | Process（行程） | Thread（執行緒） |
|----------|----------------|------------------|
| 位址空間 | 各自獨立 | 共享同一位址空間 |
| 資源消耗 | 高（建立成本大） | 低（輕量級） |
| 通訊方式 | IPC（pipe, msg, shm） | 直接讀寫共享變數 |
| 隔離性 | 高（一個 crash 不影響其他） | 低（一個 crash 整個 process 掛） |
| Context Switch 成本 | 高（需切換位址空間） | 低（僅需切換暫存器與 stack） |
| 建立速度 | 慢 | 快 |

### 1.3 Thread 的使用情境

- **平行計算**：多核心 CPU 上同時處理運算任務
- **I/O 密集型應用**：一個 thread 等待 I/O 時，其他 thread 可繼續執行
- **伺服器並行處理**：一個 thread 處理一個客戶端連線
- **GUI 應用**：主 thread 負責 UI 事件，背景 thread 處理耗時操作

### 1.4 POSIX Threads (pthreads) 範例

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_THREADS 4

void *hello(void *arg) {
    int id = *(int *)arg;
    printf("Thread %d: Hello from thread!\n", id);
    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];
    int ids[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        ids[i] = i;
        pthread_create(&threads[i], NULL, hello, &ids[i]);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("All threads completed.\n");
    return 0;
}
```

編譯方式：`gcc -pthread program.c -o program`

### 1.5 Thread 的生命週期

```
   Created（建立） ──→ Runnable（就緒）
                            │
                            ▼
                        Running（執行中）
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              Blocked（阻塞）   Terminated（終止）
                    │
                    └──→ Runnable ──→ ...
```

- **Created**：`pthread_create()` 後
- **Runnable**：準備好可被排程執行
- **Running**：正在 CPU 上執行
- **Blocked**：等待 I/O、鎖或其他資源
- **Terminated**：執行完畢或被取消

### 1.6 使用者層級 vs 核心層級 Thread

| 特性 | 使用者層級 Thread (ULT) | 核心層級 Thread (KLT) |
|------|------------------------|----------------------|
| 管理方式 | 使用者空間的 thread library | 作業系統核心負責 |
| Context Switch | 不需 kernel 介入，速度極快 | 需要 kernel 介入，速度較慢 |
| 多核心利用 | 無法利用多核心（kernel 只看得到單一 process） | 可分散到多個核心 |
| 阻塞行為 | 一個 thread 阻塞 → 整個 process 阻塞 | 一個 thread 阻塞 → 其他 thread 仍可執行 |
| 實例 | green threads, GNU pth | Windows threads, Linux pthreads (NPTL) |

現代 Linux 使用 NPTL（Native POSIX Thread Library），提供 1:1 的核心層級 thread 對應。

---

## 2. Race Condition（競爭條件）

### 2.1 什麼是 Race Condition？

**Race Condition（競爭條件）** 發生在多個 thread（或 process）同時存取共享資料，且最終結果取決於執行順序（timing）的情況。當執行順序不同導致不同結果時，就表示存在 race condition。

### 2.2 經典範例：計數器

```c
int counter = 0;

// Thread A                        // Thread B
counter++;                          counter--;
```

看似簡單的 `counter++`，在機器碼層級其實是**三條指令**：

```asm
load  counter, %reg    ; 從記憶體載入 counter 到暫存器
add   %reg, 1          ; 暫存器 + 1
store %reg, counter    ; 寫回記憶體
```

若 Thread A 與 Thread B 交錯執行：

```
時間  Thread A                  Thread B
 1    load counter (0)
 2                              load counter (0)
 3    add => reg=1
 4                              sub => reg=-1
 5    store counter = 1
 6                              store counter = -1
```

結果 `counter = -1`（期望值為 0），資料已毀損。

### 2.3 Race Condition 的三個必要條件

1. **共享資源**（Shared Resource）：多個 thread 可同時存取的變數或資料結構
2. **非原子操作**（Non-atomic Operation）：存取操作可被中斷
3. **交錯執行**（Interleaving）：排程器可能在操作中途切換 thread

### 2.4 更多 Race Condition 範例

#### 案例 1：檢查後使用（TOCTOU）

```c
// 看似安全，實則有 race
if (access("file", W_OK) == 0) {  // 檢查
    // 此時可能被其他 thread 或 process 置換檔案
    FILE *f = fopen("file", "w");  // 使用
}
```

這稱為 **TOCTOU（Time of Check to Time of Use）** 漏洞。

#### 案例 2：延遲初始化

```c
static int *data = NULL;

void get_data() {
    if (data == NULL) {        // Thread A 與 Thread B 可能同時進入
        data = malloc(1000);   // 造成兩次 allocation，且其中一次被覆蓋（記憶體洩漏）
    }
    return data;
}
```

#### 案例 3：鏈表操作

```c
// 兩個 thread 同時對鏈表插入節點
void insert(node_t *prev, node_t *new) {
    new->next = prev->next;     // 若在此行中斷...
    prev->next = new;           // 另一 thread 的操作可能被覆蓋
}
```

### 2.5 Race Condition 的偵測

- **靜態分析工具**：檢查可能的資料競爭（如 ThreadSanitizer）
- **動態分析工具**：執行時期偵測（如 Valgrind --tool=helgrind）
- **Code Review**：人眼檢查共享資源存取是否有保護

#### 使用 ThreadSanitizer 範例

```bash
gcc -fsanitize=thread -g program.c -o program -lpthread
./program
```

### 2.6 為什麼 Race Condition 很難除錯？

- **不確定性**：每次執行結果可能不同
- **難以重現**：依賴特定的排程時機
- **Heisenbug**：加入除錯程式碼可能會改變 timing，使 bug 消失
- **時序敏感**：可能在開發環境從不發生，但在正式環境頻繁發生

---

## 3. Mutex（互斥鎖）

### 3.1 什麼是 Mutex？

**Mutex（Mutual Exclusion，互斥鎖）** 是一種同步機制，用來保護共享資源，確保**同一時間只有一個 thread** 可以存取被保護的臨界區段（Critical Section）。

```
              Thread A          Thread B
Lock(mutex) ──────┐
                  ▼
            臨界區段（counter++）
                  │
Unlock(mutex) ────┘
                                  Lock(mutex) ── 等待中...
                                              │
                                              ▼
                                        臨界區段
                                              │
                                  Unlock(mutex)
```

### 3.2 Mutex 的操作

Mutex 提供兩個原子操作：

| 操作 | 行為 |
|------|------|
| `lock(m)` | 取得鎖。若鎖已被佔用，則**阻塞**直到鎖可用 |
| `unlock(m)` | 釋放鎖。若有其他 thread 正在等待，喚醒其中一個 |

### 3.3 pthread Mutex 使用範例

```c
#include <pthread.h>
#include <stdio.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int counter = 0;

void *worker(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        pthread_mutex_lock(&mutex);
        counter++;                    // 臨界區段
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("Final counter: %d (expected: 2000000)\n", counter);
    return 0;
}
```

若拿掉 mutex，結果將遠低於 2000000。

### 3.4 Mutex 的實作原理

Mutex 底層依賴硬體提供的**原子指令**：

#### Test-and-Set (x86: `xchg`)

```c
int test_and_set(int *lock) {
    int old = *lock;
    *lock = 1;           // 原子操作：讀取舊值並設為 1
    return old;
}

void lock(mutex_t *m) {
    while (test_and_set(&m->flag) == 1)
        ; // busy wait (spin)
}

void unlock(mutex_t *m) {
    m->flag = 0;
}
```

#### Compare-and-Swap (x86: `cmpxchg`)

```c
int compare_and_swap(int *ptr, int expected, int new) {
    int old = *ptr;
    if (old == expected)
        *ptr = new;      // 原子操作
    return old;
}
```

### 3.5 Spinlock vs Mutex

| 特性 | Spinlock | Mutex |
|------|----------|-------|
| 等待行為 | 不斷迴圈檢查（busy wait） | thread 被阻塞，讓出 CPU |
| 適用場景 | 鎖定時間極短（< context switch 時間） | 鎖定時間較長 |
| CPU 使用 | 等待時持續佔用 CPU | 等待時不佔用 CPU |
| Context Switch | 不會發生 | 會發生 |

**實務建議**：
- 鎖定時間短 → Spinlock（如核心程式碼）
- 鎖定時間長 → Mutex（如使用者程式）

### 3.6 Mutex 的種類

| 類型 | 說明 |
|------|------|
| 一般 Mutex（Normal） | 同一個 thread 重複 lock 會 deadlock |
| 遞迴 Mutex（Recursive） | 同一個 thread 可重複 lock，需相同次數 unlock |
| 錯誤檢查 Mutex（Error Check） | 重複 lock 會回傳錯誤而不 deadlock |
| 適應性 Mutex（Adaptive） | 先 spin 一段時間，若鎖仍無法取得則阻塞 |

### 3.7 常見的 Mutex 使用錯誤

#### 忘記解鎖

```c
void func() {
    pthread_mutex_lock(&m);
    if (some_error) {
        return;           // ❌ 忘記 unlock，造成死結
    }
    pthread_mutex_unlock(&m);
}
```

#### 重複鎖定（非遞迴 mutex）

```c
void inner() {
    pthread_mutex_lock(&m);  // 第二次 lock（同一個 thread）
    // ...
    pthread_mutex_unlock(&m);
}

void outer() {
    pthread_mutex_lock(&m);
    inner();                // ❌ 導致 deadlock
    pthread_mutex_unlock(&m);
}
```

#### 解鎖別人的鎖

```c
// Thread A                    // Thread B
lock(m);                       lock(m);
unlock(m);                     // ❌ 無法取得鎖
// ...
                               // Thread A 不小心 unlock 了 Thread B 的鎖？
```

### 3.8 RAII 風格的 Mutex 管理

在 C++ 中，使用 RAII（Resource Acquisition Is Initialization）自動管理鎖：

```cpp
// C++
{
    std::lock_guard<std::mutex> guard(m);
    // 臨界區段：離開作用域時自動 unlock
}
```

在 C 中可模擬類似模式：

```c
// 使用 goto cleanup 模式
void func() {
    pthread_mutex_lock(&m);
    if (error) goto cleanup;
    // ... 正常工作
cleanup:
    pthread_mutex_unlock(&m);
}
```

---

## 4. Deadlock（死結）

### 4.1 什麼是 Deadlock？

**Deadlock（死結）** 是指一組 thread（或 process）中的每一個都在等待另一個 thread 持有的資源，導致所有 thread 永遠無法繼續執行的狀態。

```
   Thread A               Thread B
      │                       │
   lock(m1) ✅             lock(m2) ✅
      │                       │
   lock(m2) ⏳ ...         lock(m1) ⏳ ...
   （等待 B 釋放 m2）      （等待 A 釋放 m1）
```

### 4.2 Deadlock 的四個必要條件（Coffman Conditions）

所有四個條件**必須同時滿足**才會發生 deadlock：

| 條件 | 說明 |
|------|------|
| **1. 互斥（Mutual Exclusion）** | 資源一次只能被一個 thread 使用 |
| **2. 持有並等待（Hold and Wait）** | Thread 持有資源的同時，還在等待其他資源 |
| **3. 不可搶佔（No Preemption）** | 資源不能被強制從 thread 手中拿走 |
| **4. 循環等待（Circular Wait）** | 存在一組 thread 形成封閉的等待環 |

### 4.3 Deadlock 範例

```c
#include <pthread.h>
#include <stdio.h>

pthread_mutex_t m1 = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t m2 = PTHREAD_MUTEX_INITIALIZER;

void *thread_a(void *arg) {
    pthread_mutex_lock(&m1);
    printf("A: 拿到 m1\n");
    sleep(1);  // 確保 B 有機會拿到 m2
    pthread_mutex_lock(&m2);  // 等待 m2（B 持有中）
    printf("A: 拿到 m2\n");
    pthread_mutex_unlock(&m2);
    pthread_mutex_unlock(&m1);
    return NULL;
}

void *thread_b(void *arg) {
    pthread_mutex_lock(&m2);
    printf("B: 拿到 m2\n");
    sleep(1);
    pthread_mutex_lock(&m1);  // 等待 m1（A 持有中）
    printf("B: 拿到 m1\n");
    pthread_mutex_unlock(&m1);
    pthread_mutex_unlock(&m2);
    return NULL;
}

int main() {
    pthread_t a, b;
    pthread_create(&a, NULL, thread_a, NULL);
    pthread_create(&b, NULL, thread_b, NULL);
    pthread_join(a, NULL);  // 永遠等不到...
    pthread_join(b, NULL);
    return 0;
}
```

執行此程式將**永遠卡住**。

### 4.4 Deadlock 的處理策略

#### 策略一：預防（Prevention）

破壞四個必要條件中的至少一個：

**破壞「互斥」**：
- 使用無鎖（lock-free）資料結構
- 使用 read-write lock（讀取不互斥）

**破壞「持有並等待」**：
- 要求 thread 一次取得所有需要的資源
- 缺點：資源利用率低，可能造成飢餓

```c
// 一次取得所有鎖
pthread_mutex_lock(&m1);
pthread_mutex_lock(&m2);  // 若失敗則釋放 m1，重試
```

**破壞「不可搶佔」**：
- 使用 `pthread_mutex_trylock()`，若無法取得則釋放已持有的鎖

```c
void *thread_a(void *arg) {
    pthread_mutex_lock(&m1);
    if (pthread_mutex_trylock(&m2) != 0) {
        pthread_mutex_unlock(&m1);  // 釋放已持有的鎖
        // 稍後重試
    }
}
```

**破壞「循環等待」**：
- 對所有鎖賦予**全域順序**（global ordering），所有 thread 按同樣順序加鎖

```c
// 所有 thread 都遵守：先鎖 m1，再鎖 m2
void *thread_a(void *arg) {
    lock(m1);
    lock(m2);   // ✅ 正確順序
}

void *thread_b(void *arg) {
    lock(m1);   // ✅ 也先鎖 m1
    lock(m2);   // ✅ 再鎖 m2
}
```

#### 策略二：避免（Avoidance）

使用**銀行家演算法（Banker's Algorithm）**，動態判斷資源分配是否會導致不安全狀態。

- 每個 thread 需事先宣告最大資源需求量
- 系統只有在分配後仍處於安全狀態時，才允許分配
- 優點：資源利用率比預防高
- 缺點：需預先知最大需求量，實務上較少使用

#### 策略三：偵測與恢復（Detection & Recovery）

允許 deadlock 發生，但偵測到後進行恢復：

**偵測方法**：
- 定期檢查**資源分配圖（Resource Allocation Graph）**是否有循環
- 若所有資源只有單一實例，循環即代表 deadlock

**恢復方法**：
1. **終止 thread**：一次終止一個 deadlock 中的 thread，直到死結解除
2. **搶佔資源**：從某個 thread 強制取走資源，分配給其他人（需實作 rollback）

#### 策略四：忽略（Ostrich Algorithm）

假設 deadlock 極少發生，不做任何處理。

> 實際上，Windows 和 Linux 對大多數使用者程式都採用此策略——因為預防和避免的成本太高，且 deadlock 通常可透過良好的程式設計習慣避免。

### 4.5 常見的 Deadlock 情境

#### 情境 1：經典的 Lock Ordering Deadlock

```
Thread 1: lock(A) → lock(B)
Thread 2: lock(B) → lock(A)
```

解法：全域統一的鎖定順序。

#### 情境 2：Thread 之間的互相等待

```
Thread 1: 發送訊息給 Thread 2，等待回覆（持有鎖 A）
Thread 2: 需要鎖 A 才能處理訊息（持有鎖 B）
```

解法：使用非同步通訊或 timeout。

#### 情境 3：遞迴 deadlock（同一 thread）

```
lock(m);
func();   // func 內部又 lock(m)
```

解法：使用 recursive mutex 或重構程式碼。

#### 情境 4：鎖 + Condition Variable 的組合

```
Thread A 持有 mutex，等待 condition
Thread B 需要同一個 mutex 才能 signal condition
```

解法：確保 pthread_cond_wait 會自動釋放 mutex。

### 4.6 Deadlock 的預防工具

- **靜態分析**：檢查 lock ordering 是否一致
- **Lockdep（Linux 核心）**：執行時期追蹤鎖的依賴關係
- **ThreadSanitizer**：可偵測某些 deadlock 模式
- **Helgrind（Valgrind）**：偵測同步錯誤，包括 deadlock

### 4.7 避免 Deadlock 的最佳實踐

1. **統一 Lock Ordering**：所有 thread 以相同順序取得鎖
2. **盡量減少鎖的持有時間**：只保護真正需要保護的程式碼
3. **使用 Lock Hierarchy**：為鎖分層級，規定只能從低層級往高層級取得
4. **使用 trylock**：搭配 backoff 與重試機制
5. **避免在持有鎖時呼叫外部 callback 或 unknown function**
6. **使用 RAII 或 finally 模式**確保解鎖
7. **審慎評估是否需要多層鎖**，必要時重構

---

## 5. 總結與對照

### 5.1 四個主題的關係圖

```
Thread（執行緒）
    │
    ├── 多個 thread 共享資源 ──→ Race Condition（競爭條件）
    │                                  │
    │                                  ▼
    │                            需要同步機制
    │                                  │
    │                                  ▼
    │                         ┌── Mutex（互斥鎖）──┐
    │                         │                     │
    │                         │               不當使用
    │                         │                     │
    │                         │                     ▼
    │                         └── Deadlock（死結）──┘
    │
    └── 每個 thread 有自己的 stack ──→ 輕量級並行
```

### 5.2 對照總結

| 主題 | 核心問題 | 解決方案 | 不當使用的後果 |
|------|---------|---------|---------------|
| **Thread** | 如何輕量級地實現並行？ | 使用 pthread / std::thread | 同步開銷、除錯困難 |
| **Race Condition** | 共享資料存取順序不確定 | 使用同步機制（mutex, semaphore 等） | 資料毀損、程式行為異常 |
| **Mutex** | 如何確保互斥存取？ | Lock / Unlock 保護臨界區段 | Deadlock、效能下降、優先權反轉 |
| **Deadlock** | 多個鎖互相等待 | 預防、避免、偵測恢復 | 程式永久卡住 |

### 5.3 關鍵 Takeaways

1. **Thread 是並行執行緒**，共享位址空間但各有獨立堆疊
2. **Race Condition 源自於非原子的共享資源存取**，必須用同步機制保護
3. **Mutex 是最基本的同步工具**，確保臨界區段的互斥性
4. **Deadlock 發生於循環等待**，最好的預防方式是**統一的鎖定順序**
5. 寫並行程式的第一原則：**先確保正確性，再考慮效能**

---

> **參考資料**
> - Operating Systems: Three Easy Pieces (Remzi & Andrea Arpaci-Dusseau)
> - Advanced Programming in the UNIX Environment (Stevens)
> - POSIX Threads Programming (IBM)
> - Linux man pages: pthreads(7), mutex(3p)
