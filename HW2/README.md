# HanScript (한글스크립트) - 韓語微型編譯器與虛擬機

HanScript 是一個基於 Python 實作的微型程式語言教學專案。本專案親手打造了完整的**詞法分析器 (Lexer)**、**語法分析器 (Parser)**、**編譯器 (Compiler)**、**堆疊虛擬機 (Stack-based VM)** 以及**抽象語法樹解譯器 (AST Walker Interpreter)**。

本語言採用**強型態（目前支援整數）**系統，無垃圾蒐集機制（GC），並使用**韓語關鍵字**作為語法核心。

---

## 🚀 語言規格與設計 (Specification)

### 1. 系統架構定義
* **型態系統：** 強型態 (Strongly Typed)，不允許隱式型態轉換。
* **執行模式：** 支援雙路線執行：
  * **路線 A (編譯模式)：** 原始碼 ➔ AST ➔ 線性位元組碼 (Bytecode) ➔ 虛擬機 (VM) 執行。
  * **路線 B (解譯模式)：** 原始碼 ➔ AST ➔ 解譯器直接走訪 (AST Walker) 執行。
* **目標機器架構：** 基於**堆疊機 (Stack Machine)** 的虛擬機，利用 `PUSH`, `POP`, `ADD`, `JUMP` 等線性指令操作資料堆疊與程式計數器 (PC)。
* **記憶體管理：** 無垃圾蒐集 (No GC)，變數存放於靜態全域符號表中。

### 2. 語法規格 (EBNF)
```ebnf
Program         ::= Statement*
Statement       ::= PrintStmt | AssignStmt | IfStmt | WhileStmt
PrintStmt       ::= "출력" Expression ";"
AssignStmt      ::= ( "변수" Identifier "=" Expression ";" ) | ( Identifier "=" Expression ";" )
IfStmt          ::= "만약" "(" Comparison ")" "{" Statement* "}"
WhileStmt       ::= "반복" "(" Comparison ")" "{" Statement* "}"
Comparison      ::= Expression ( ( ">" | "<" | "==" ) Expression )?
Expression      ::= Term ( ( "+" | "-" ) Term )*
Term            ::= Factor ( ( "*" | "/" ) Factor )*
Factor          ::= Number | Identifier | "(" Comparison ")"
Identifier      ::= [가-힣a-zA-Z_][가-힣a-zA-Z0-9_]*
Number          ::= [0-9]+