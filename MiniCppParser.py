# mcparser.py
'''
Analizador Sintactico (LALR)
'''

from rich import print
import sly
from MiniCppAST import *
from MiniCppLex import Lexer

class Parser(sly.Parser):
    debugfile = 'minicc.txt'

    tokens = Lexer.tokens

    precedence = (
        ('left', 'POINT'),
        ('right', 'IF'),  
        ('left', 'ELSE'),
        ('left', 'PLUSPLUS'), 
        ('left', 'MINUSMINUS'),
        ('right', 'PLUSEQ'),
        ('right', 'MINUSEQ'),
        ('right', 'MULEQ'),
        ('right', 'DIVEQ'),  
        ('right', '='),
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE'),
        ('left', '<', 'LE', '>', 'GE'),
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('right', 'UMINUS', '!'),
    )

    @_("decl_list")
    def program(self, p):
        return Program(p.decl_list)

    @_("decl_list decl")
    def decl_list(self, p):
        return p.decl_list + [ p.decl ]
    
    @_("decl")
    def decl_list(self, p):
        return [ p.decl ]

    @_("var_decl", "func_decl", "class_decl")
    def decl(self, p):
        return p[0]
    
    @_("CLASS IDENT sclass_opt '{' class_body '}' ';'")
    def class_decl(self, p):
        return ClassDeclStmt(p.IDENT, p.sclass_opt, p.class_body)
    
    @_("empty")
    def sclass_opt(self, p):
        return None
    
    @_("':' IDENT")
    def sclass_opt(self, p):
        return p.IDENT

    @_("class_member_list")
    def class_body(self, p):
        return p.class_member_list

    @_("class_member_list class_member")
    def class_member_list(self, p):
        return p.class_member_list + [ p.class_member ]

    @_("class_member")
    def class_member_list(self, p):
        return [ p.class_member ]

    @_("method_decl")
    def class_member(self, p):
        return p[0]
    
    @_("type_spec IDENT '(' [ params ] ')' compound_stmt")
    def method_decl(self, p):
        return FuncDeclStmt(p.type_spec, p.IDENT, p.params, p.compound_stmt)
    
    @_("type_spec IDENT [ '=' expr ] ';'")
    def var_decl(self, p):
        return VarDeclStmt(p.type_spec, p.IDENT, p.expr)
    
    @_("type_spec IDENT '[' ']' ';'")
    def var_decl(self, p):
        return ArrayDeclStmt(p.type_spec, p.IDENT)
    
    @_("VOID", "BOOL", "INT", "FLOAT", "STR")
    def type_spec(self, p):
        return p[0]
    
    @_("type_spec IDENT '(' [ params ] ')' compound_stmt")
    def func_decl(self, p):
        return FuncDeclStmt(p.type_spec, p.IDENT, p.params, p.compound_stmt)
    
    @_("param_list")
    def params(self, p):
        return p.param_list
    
    @_("VOID")
    def params(self, p):
        return []
    
    @_("param_list ',' param")
    def param_list(self, p):
        return p.param_list + [p.param]
    
    @_("param")
    def param_list(self, p):
        return [p.param]
    
    @_("type_spec IDENT")
    def param(self, p):
        return VarDeclStmt(p.type_spec, p.IDENT, None)

    @_("type_spec IDENT '[' ']'")
    def param(self, p):
        return ArrayDeclStmt(p.type_spec, p.IDENT, True)

    @_("'{' local_decls stmt_list '}'")
    def compound_stmt(self, p):
        return CompoundStmt(p.local_decls, p.stmt_list)
    
    @_("local_decl_list")
    def local_decls(self, p):
        return p.local_decl_list
    
    @_("empty")
    def local_decls(self, p):
        return []
    
    @_("local_decl_list local_decl")
    def local_decl_list(self, p):
        return p.local_decl_list + [p.local_decl]
    
    @_("local_decl")
    def local_decl_list(self, p):
        return [p.local_decl]
    
    @_("type_spec IDENT [ '=' expr ] ';'")
    def local_decl(self, p):
        return VarDeclStmt(p.type_spec, p.IDENT, p.expr)
    
    @_("type_spec IDENT '[' ']' ';'")
    def local_decl(self, p):
        return ArrayDeclStmt(p.type_spec, p.IDENT)
    
    @_("stmt_list stmt")
    def stmt_list(self, p):
        return p.stmt_list + [p.stmt]
    
    @_("stmt")
    def stmt_list(self, p):
        return [p.stmt]
    
    @_("expr_stmt",
       "compound_stmt",
       "if_stmt",
       "while_stmt",
       "return_stmt",
       "break_stmt",
       "for_stmt",
       "printf_stmt",
       "scanf_stmt",
       "sprintf_stmt")
    def stmt(self, p):
        return p[0]
    
    @_("expr ';'")
    def expr_stmt(self, p):
        return ExprStmt(p.expr)

    @_("';'")
    def expr_stmt(self, p):
        return NullStmt()
    
    @_("WHILE '(' expr ')' compound_stmt")
    def while_stmt(self, p):
        return WhileStmt(p.expr, p.compound_stmt)
    
    @_("FOR '(' expr ';' expr ';' expr ')' compound_stmt")
    def for_stmt(self, p):
        return ForStmt(p.expr0, p.expr1, p.expr2, p.compound_stmt)
    
    @_("FOR '(' local_decl expr ';' expr ')' compound_stmt")
    def for_stmt(self, p):
        return ForStmt(p.local_decl, p.expr0, p.expr1, p.compound_stmt)

    @_("IF '(' expr ')' compound_stmt %prec IF")
    def if_stmt(self, p):
        return IfStmt(p.expr, p.compound_stmt, None)

    @_("IF '(' expr ')' compound_stmt ELSE compound_stmt")
    def if_stmt(self, p):
        return IfStmt(p.expr, p.compound_stmt0, p.compound_stmt1)
    
    @_("RETURN ';'")
    def return_stmt(self, p):
        return ReturnStmt()
    
    @_("RETURN expr ';'")
    def return_stmt(self, p):
        return ReturnStmt(p.expr)
    
    @_("BREAK ';'")
    def break_stmt(self, p):
        return BreakStmt()
    
    @_("CONTINUE ';'")
    def break_stmt(self, p):
        return ContinueStmt()
    
    @_("IDENT '=' expr")
    def expr(self, p):
        return VarAssignmentExpr(p.IDENT, p.expr)

    @_("IDENT '[' expr ']' '=' expr")
    def expr(self, p):
        return ArrayAssignmentExpr(p.IDENT, p.expr0, p.expr1)
    
    @_("THIS")
    def expr(self, p):
        return This()
    
    @_("expr POINT IDENT '=' expr")
    def expr(self, p):
        return Set(p.expr0, p.IDENT, p.expr1)
    
    @_("expr EQ expr",
       "expr NE expr",
       "expr LE expr",
       "expr '<' expr",
       "expr GE expr",
       "expr '>' expr",
       "expr '+' expr",
       "expr '-' expr",
       "expr '*' expr",
       "expr '/' expr",
       "expr '%' expr")
    def expr(self, p):
        return BinaryOpExpr(p[1], p.expr0, p.expr1)
    
    @_("expr OR expr",
       "expr AND expr")
    def expr(self, p):
        return LogicalOpExpr(p[1], p.expr0, p.expr1)
    

    @_("'!' expr",
       "'-' expr %prec UMINUS",
       "'+' expr %prec UMINUS")
    def expr(self, p):
        return UnaryOpExpr(p[0], p.expr)
    
    @_("'(' expr ')'")
    def expr(self, p):
        return Grouping(p.expr)

    @_("IDENT")
    def expr(self, p):
        return VarExpr(p.IDENT)

    @_("IDENT '[' expr ']'")
    def expr(self, p):
        return ArrayLoockupExpr(p.IDENT, p.expr)

    @_("IDENT '(' args ')'")
    def expr(self, p):
        return CallExpr(p.IDENT, p.args)
    
    @_("SIZE '(' IDENT ')'")
    def expr(self, p):
        return SizeOfExpr(p.IDENT)
    
    @_("SUPER POINT IDENT")
    def expr(self, p):
        return Super(p.IDENT)
    
    @_("expr POINT IDENT")
    def expr(self, p):
        return Get(p.expr, p.IDENT)
    
    @_("INTTOFLOAT '(' expr ')'")
    def expr(self, p):
        return IntToFloatExpr(p.expr)
    
    @_("CAST type_spec '(' expr ')'")
    def expr(self, p):
        return CastExpr(p.type_spec, p.expr)

    @_("BOOL_LIT", "INT_LIT", "FLOAT_LIT", "STRING")
    def expr(self, p):
        return ConstExpr(p[0])

    @_("NEW type_spec '[' expr ']'")
    def expr(self, p):
        return NewArrayExpr(p.type_spec, p.expr)
    
    @_("arg_list", "empty")
    def args(self, p):
        return p[0]

    @_("arg_list ',' expr")
    def arg_list(self, p):
        return p.arg_list + [p.expr]
    
    @_("expr")
    def arg_list(self, p):
        return [p.expr]
    
    @_("expr PLUSPLUS")
    def expr(self, p):
        return PostInc(p[1], p.expr)
    
    @_("expr MINUSMINUS")
    def expr(self, p):
        return PostDec(p[1], p.expr)

    @_("PLUSPLUS expr")
    def expr(self, p):
        return PreInc(p[0], p.expr)
    
    @_("MINUSMINUS expr")
    def expr(self, p):
        return PreDec(p[0], p.expr)
    
    @_("expr PLUSEQ expr",
       "expr MINUSEQ expr",
       "expr MULEQ expr",
       "expr DIVEQ expr")
    def expr(self, p):
        return OperatorAssign(p[1], p.expr0, p.expr1)
    
    @_("PRINTF '(' STRING ')' ';' ") 
    def printf_stmt(self, p):
        return PrintfStmt(p.STRING, [])

    @_("PRINTF '(' STRING ',' arg_list ')' ';' ")
    def printf_stmt(self, p):
        return PrintfStmt(p.STRING, p.arg_list)
    
    @_("AMPERSAND expr")
    def arg_listSCANF(self, p):
        return [p.expr]
    
    @_("arg_listSCANF ',' AMPERSAND expr")
    def arg_listSCANF(self, p):
        return p.arg_listSCANF + [p.expr]
    
    @_("SCANF '(' STRING ',' arg_listSCANF ')' ';' ")
    def scanf_stmt(self, p):
        return ScanfStmt(p.STRING, p.arg_listSCANF)
    
    @_("SPRINTF '(' IDENT ',' STRING ',' arg_list ')' ';' ")
    def sprintf_stmt(self, p):
        return SprintfStmt(p.IDENT, p.STRING, p.arg_list)
    
    @_("ARRAYSIZE '(' IDENT ')'")
    def expr(self, p):
        return ArraySizeExpr(p.IDENT)
        
    @_("")
    def empty(self, p):
        return None

    def error(self, p):
        if p:
            print(f"Línea {p.lineno}: Error de sintaxis en '{p.value}'")
        else:
            print("Error de sintaxis en EOF")

def parse(source):
    lex = Lexer()
    pas = Parser()
    
    program = pas.parse(lex.tokenize(source))
    return program

if __name__ == '__main__':
    import sys

    source_code = open(sys.argv[1], encoding='utf-8').read()
    program = parse(source_code)
    if program:
        render_tree = RenderTreeVisitor()
        render_tree.render(program)
    else:
        print("[red]No se ha creado el arbol[/red]")