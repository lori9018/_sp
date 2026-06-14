import re
import re
import sys   # 新增這行：用來接收命令列參數
import os    # 新增這行：用來檢查檔案是否存在
# ==========================================
# 1. 詞法分析器 (Lexer)
# ==========================================
class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.token_specification = [
            ('NUMBER',   r'\d+'),
            ('IF',       r'만약'),       # if
            ('WHILE',    r'반복'),       # 新增：while
            ('PRINT',    r'출력'),
            ('VAR',      r'변수'),
            ('IDENT',    r'[가-힣a-zA-Z_][가-힣a-zA-Z0-9_]*'),
            ('COMPARE',  r'>|<|=='),
            ('ASSIGN',   r'='),
            ('END',      r';'),
            ('OP',       r'[+\-*/]'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('LBRACE',   r'\{'),
            ('RBRACE',   r'\}'),
            ('SKIP',     r'[ \t\n]+'),
            ('MISMATCH', r'.'),
        ]
    
    def tokenize(self):
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)
        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP': continue
            elif kind == 'MISMATCH': raise RuntimeError(f'無法識別的字元: {value}')
            self.tokens.append((kind, value))
        self.tokens.append(('EOF', ''))
        return self.tokens

# ==========================================
# 2. 語法分析器 (Parser)
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def match(self, expected_kind):
        if self.tokens[self.pos][0] == expected_kind:
            val = self.tokens[self.pos][1]
            self.pos += 1
            return val
        raise SyntaxError(f'預期 {expected_kind} 但獲得 {self.tokens[self.pos][0]}')

    def parse(self):
        statements = []
        while self.tokens[self.pos][0] != 'EOF':
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        token_type = self.tokens[self.pos][0]
        if token_type == 'PRINT': return self.parse_print()
        elif token_type == 'VAR': return self.parse_assign()
        elif token_type == 'IF':  return self.parse_if()
        elif token_type == 'WHILE': return self.parse_while() # 新增：解析 while
        else:
            # 支援直接對已經存在的變數重新賦值 (不用加 '변수' 關鍵字)
            if token_type == 'IDENT' and self.tokens[self.pos+1][0] == 'ASSIGN':
                return self.parse_reassign()
            raise SyntaxError(f'無效的語句開頭: {self.tokens[self.pos]}')

    def parse_reassign(self):
        var_name = self.match('IDENT')
        self.match('ASSIGN')
        expr = self.parse_comparison()
        self.match('END')
        return ('ASSIGN_STMT', var_name, expr)

    def parse_assign(self):
        self.match('VAR')
        var_name = self.match('IDENT')
        self.match('ASSIGN')
        expr = self.parse_comparison()
        self.match('END')
        return ('ASSIGN_STMT', var_name, expr)

    def parse_if(self):
        self.match('IF')
        self.match('LPAREN')
        condition = self.parse_comparison()
        self.match('RPAREN')
        self.match('LBRACE')
        body = []
        while self.tokens[self.pos][0] != 'RBRACE':
            if self.tokens[self.pos][0] == 'EOF': raise SyntaxError("預期 '}' 但遇到檔案結尾")
            body.append(self.parse_statement())
        self.match('RBRACE')
        return ('IF_STMT', condition, body)

    def parse_while(self):
        self.match('WHILE')
        self.match('LPAREN')
        condition = self.parse_comparison()
        self.match('RPAREN')
        self.match('LBRACE')
        body = []
        while self.tokens[self.pos][0] != 'RBRACE':
            if self.tokens[self.pos][0] == 'EOF': raise SyntaxError("預期 '}' 但遇到檔案結尾")
            body.append(self.parse_statement())
        self.match('RBRACE')
        return ('WHILE_STMT', condition, body)

    def parse_print(self):
        self.match('PRINT')
        expr = self.parse_comparison()
        self.match('END')
        return ('PRINT_STMT', expr)

    def parse_comparison(self):
        left = self.parse_expression()
        if self.tokens[self.pos][0] == 'COMPARE':
            op = self.match('COMPARE')
            right = self.parse_expression()
            left = ('COMPARE', op, left, right)
        return left

    def parse_expression(self):
        left = self.parse_term()
        while self.tokens[self.pos][0] == 'OP' and self.tokens[self.pos][1] in ('+', '-'):
            op = self.match('OP')
            right = self.parse_term()
            left = ('BIN_OP', op, left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.tokens[self.pos][0] == 'OP' and self.tokens[self.pos][1] in ('*', '/'):
            op = self.match('OP')
            right = self.parse_factor()
            left = ('BIN_OP', op, left, right)
        return left

    def parse_factor(self):
        kind, val = self.tokens[self.pos]
        if kind == 'NUMBER':
            self.pos += 1
            return ('NUM', int(val))
        elif kind == 'IDENT':
            self.pos += 1
            return ('VAR_REF', val)
        elif kind == 'LPAREN':
            self.match('LPAREN')
            expr = self.parse_comparison()
            self.match('RPAREN')
            return expr
        raise SyntaxError(f'語法錯誤於: {val}')

# ==========================================
# 3. 編譯器 (Compiler)
# ==========================================
class Compiler:
    def __init__(self):
        self.bytecode = []

    def compile(self, ast):
        for stmt in ast:
            self.visit(stmt)
        return self.bytecode

    def visit(self, node):
        node_type = node[0]
        if node_type == 'NUM': self.bytecode.append(['PUSH', node[1]])
        elif node_type == 'VAR_REF': self.bytecode.append(['LOAD', node[1]])
        elif node_type == 'COMPARE':
            self.visit(node[2])
            self.visit(node[3])
            self.bytecode.append(['COMPARE', node[1]])
        elif node_type == 'BIN_OP':
            self.visit(node[2])
            self.visit(node[3])
            if node[1] == '+': self.bytecode.append(['ADD'])
            elif node[1] == '-': self.bytecode.append(['SUB'])
            elif node[1] == '*': self.bytecode.append(['MUL'])
            elif node[1] == '/': self.bytecode.append(['DIV'])
        elif node_type == 'ASSIGN_STMT':
            self.visit(node[2])
            self.bytecode.append(['STORE', node[1]])
        elif node_type == 'PRINT_STMT':
            self.visit(node[1])
            self.bytecode.append(['PRINT'])
        elif node_type == 'IF_STMT':
            self.visit(node[1])
            jump_idx = len(self.bytecode)
            self.bytecode.append(['JUMP_IF_FALSE', 0]) 
            for stmt in node[2]: self.visit(stmt)
            self.bytecode[jump_idx][1] = len(self.bytecode) 
            
        elif node_type == 'WHILE_STMT':
            # 1. 標記迴圈條件判斷的開頭位置
            loop_start_idx = len(self.bytecode)
            
            # 2. 產生條件判斷的指令
            self.visit(node[1]) 
            
            # 3. 插入條件不成立時跳出迴圈的指令 (佔位符)
            exit_jump_idx = len(self.bytecode)
            self.bytecode.append(['JUMP_IF_FALSE', 0]) 
            
            # 4. 產生迴圈內部的指令
            for stmt in node[2]: 
                self.visit(stmt)
                
            # 5. 迴圈內部執行完後，無條件跳回迴圈開頭！
            self.bytecode.append(['JUMP', loop_start_idx])
            
            # 6. 修補：將條件不成立時的跳出位置填入 (跳過剛剛的 JUMP)
            self.bytecode[exit_jump_idx][1] = len(self.bytecode)

# ==========================================
# 4. 堆疊虛擬機 (Stack-Based VM)
# ==========================================
class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.memory = {}

    def execute(self, bytecode):
        pc = 0 
        while pc < len(bytecode):
            instr = bytecode[pc]
            op = instr[0]
            
            if op == 'PUSH':
                self.stack.append(instr[1])
                pc += 1
            elif op == 'LOAD':
                self.stack.append(self.memory[instr[1]])
                pc += 1
            elif op == 'STORE':
                self.memory[instr[1]] = self.stack.pop()
                pc += 1
            elif op == 'COMPARE':
                b, a = self.stack.pop(), self.stack.pop()
                if instr[1] == '>': self.stack.append(1 if a > b else 0)
                elif instr[1] == '<': self.stack.append(1 if a < b else 0)
                elif instr[1] == '==': self.stack.append(1 if a == b else 0)
                pc += 1
            elif op == 'JUMP_IF_FALSE':
                condition = self.stack.pop()
                if condition == 0: pc = instr[1] # 條件為否，跳躍
                else: pc += 1                    # 條件為真，繼續
            elif op == 'JUMP':                   # 新增：無條件跳躍
                pc = instr[1]
            elif op == 'ADD':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
                pc += 1
            elif op == 'SUB':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
                pc += 1
            elif op == 'MUL':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
                pc += 1
            elif op == 'DIV':
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a // b)
                pc += 1
            elif op == 'PRINT':
                print(f"[VM 輸出] -> {self.stack.pop()}")
                pc += 1

# ==========================================
# 5. 解譯器 (AST Walker Interpreter)
# ==========================================
class Interpreter:
    def __init__(self):
        self.memory = {}

    def interpret(self, ast):
        for stmt in ast:
            self.execute(stmt)

    def execute(self, node):
        node_type = node[0]
        if node_type == 'ASSIGN_STMT':
            self.memory[node[1]] = self.evaluate(node[2])
        elif node_type == 'PRINT_STMT':
            print(f"[解譯器輸出] -> {self.evaluate(node[1])}")
        elif node_type == 'IF_STMT':
            if self.evaluate(node[1]): 
                for stmt in node[2]: self.execute(stmt)
        elif node_type == 'WHILE_STMT':
            # 解譯器最簡單，直接借用 Python 自己的 while
            while self.evaluate(node[1]):
                for stmt in node[2]: self.execute(stmt)

    def evaluate(self, node):
        node_type = node[0]
        if node_type == 'NUM': return node[1]
        elif node_type == 'VAR_REF': return self.memory[node[1]]
        elif node_type == 'COMPARE':
            left, right = self.evaluate(node[2]), self.evaluate(node[3])
            if node[1] == '>': return left > right
            elif node[1] == '<': return left < right
            elif node[1] == '==': return left == right
        elif node_type == 'BIN_OP':
            left, right = self.evaluate(node[2]), self.evaluate(node[3])
            if node[1] == '+': return left + right
            elif node[1] == '-': return left - right
            elif node[1] == '*': return left * right
            elif node[1] == '/': return left // right

# ==========================================
# 6. 執行測試 (讀取外部檔案)
# ==========================================
if __name__ == '__main__':
    # 1. 檢查使用者是否有輸入檔案路徑
    if len(sys.argv) < 2:
        print("❌ 錯誤：請提供要執行的 HanScript 檔案路徑！")
        print("👉 用法示範：python hanscript.py examlp_/example1")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    # 2. 檢查該檔案是否存在
    if not os.path.exists(file_path):
        print(f"❌ 錯誤：找不到檔案 '{file_path}'")
        sys.exit(1)
        
    # 3. 讀取檔案內容
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
        
    print(f"📂 正在執行檔案: {file_path}")
    print("-" * 30)
    
    # 4. 開始解析與執行
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        print("=== [路線 A] 虛擬機執行 (Compiler + VM) ===")
        compiler = Compiler()
        bytecode = compiler.compile(ast)
        vm = VirtualMachine()
        vm.execute(bytecode)

        print("\n=== [路線 B] 解譯器執行 ===")
        interpreter = Interpreter()
        interpreter.interpret(ast)
        
    except Exception as e:
        print(f"\n❌ 執行時發生錯誤: {e}")