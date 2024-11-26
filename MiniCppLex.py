# mclex
'''
Analizador Léxico para Mini-C++
'''

from rich import print
import sly
import re

class Lexer(sly.Lexer):

    tokens = {
        # palabras reservadas
        'VOID', 'BOOL', 'INT', 'FLOAT', 'IF', 'ELSE', 'WHILE', 'RETURN', 'SPRINTF', 'INTTOFLOAT', 'CAST',
        'BREAK', 'CONTINUE', 'SIZE', 'NEW', 'CLASS', 'FOR', 'PRINTF', 'SCANF', 'SUPER', 'THIS', 'POINT',

        # Operadores de Relacion
        'AND', 'OR', 'EQ', 'NE', 'GE', 'LE', 

        # Otros Simbolos
        'IDENT', 'BOOL_LIT', 'INT_LIT', 'FLOAT_LIT', 'STRING',
        'PLUSPLUS', 'MINUSMINUS', 'PLUSEQ', 'MINUSEQ', 'MULEQ', 'DIVEQ',

    }
    literals = '+-*/%=().,;{}[]<>!'
    
    # operadores de asignacion
    PLUSEQ = r'\+='
    MINUSEQ = r'-='
    MULEQ = r'\*='
    DIVEQ = r'/='
    
    # operadores unarios
    PLUSPLUS = r'\+\+'
    MINUSMINUS = r'--'

    # Ignorar patrones dentro del archivo fuente
    ignore = ' \t'
    
    #Otros operadores
    POINT = r'\.'

    # Ignorar saltos de linea
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    # Ignorar Comentarios
    @_(r'//.*\n')
    def ignore_cppcomment(self, t):
        self.lineno += 1

    @_(r'/\*(.|\n)*?\*/')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    # Operadores de Relacion
    LE = r'<='
    GE = r'>='
    EQ = r'=='
    NE = r'!='

    # Operadores Lógicos
    OR  = r'\|\|'
    AND = r'&&'

    # Definición de Tokens
    IDENT = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # Casos Especiales (Palabras reservadas)
    IDENT['break']    = 'BREAK'
    IDENT['continue'] = 'CONTINUE'
    IDENT['void']     = 'VOID'
    IDENT['bool']     = 'BOOL' 
    IDENT['int']      = 'INT' 
    IDENT['float']    = 'FLOAT'
    IDENT['if']       = 'IF'
    IDENT['else']     = 'ELSE' 
    IDENT['while']    = 'WHILE'
    IDENT['return']   = 'RETURN'
    IDENT['size']     = 'SIZE'
    IDENT['new']      = 'NEW'
    IDENT['true']     = 'BOOL_LIT'
    IDENT['false']    = 'BOOL_LIT'
    IDENT['class']    = 'CLASS'
    IDENT['for']      = 'FOR'
    IDENT['printf']   = 'PRINTF'
    IDENT['scanf']    = 'SCANF'
    IDENT['sprintf']  = 'SPRINTF'
    IDENT['IntToFloat'] = 'INTTOFLOAT'
    IDENT['cast']     = 'CAST'

    @_(r'((0(?!\d))|([1-9]\d*))((\.\d+(e[-+]?\d+)?)|([eE][-+]?\d+))')
    def FLOAT_LIT(self, t):
        t.value = float(t.value)
        return t

    @_(r'(0\d+)((\.\d+(e[-+]?\d+)?)|(e[-+]?\d+))')
    def malformed_fnumber(self, t):
        print(f"{self.lineno}: Literal de punto flotante '{t.value}' no sportado")

    @_(r'0(?!\d)|([1-9]\d*)')
    def INT_LIT(self, t):
        t.value = int(t.value)
        return t

    @_(r'0\d+')
    def malformed_inumber(self, t):
        print(f"{self.lineno}: Literal entera '{t.value}' no sportado")

    @_(r'"([^"\\]|\\.)*"')
    def STRING(self, t):
        t.value = self.unescape(t.value[1:-1])
        return t

    def unescape(self, s):
        "Convierte caracteres de escape a sus valores reales."
        escapes = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\\\': '\\',
            '\\"': '"',
            "\\'": "'",
        }
        for esc, char in escapes.items():
            s = s.replace(esc, char)
        return s
    

    def error(self, t):
        print(f"{self.lineno}: El caracter '{t.value[0]}' no es permitido")
        self.index += 1

def print_lexer(source):
    from rich.table   import Table
    from rich.console import Console

    lex = Lexer()

    table = Table(title='Análisis Léxico')
    table.add_column('type')
    table.add_column('value')
    table.add_column('lineno', justify='right')

    for tok in lex.tokenize(source):
        value = tok.value if isinstance(tok.value, str) else str(tok.value)
        table.add_row(tok.type, value, str(tok.lineno))
    
    console = Console()
    console.print(table)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print(f"Usage MiniCppLex.py textfile")
        exit(1)
        
    print_lexer(open(sys.argv[1], encoding='utf-8').read())