# mccast.py
'''
Estructura del AST (básica). 

Debe agregar las clases que considere que hacen falta.

Statement
 |
 +--- NullStmt
 |
 +--- ExprStmt
 |
 +--- IfStmt
 |
 +--- WhileStmt
 |
 +--- ReturnStmt
 |
 +--- BreakStmt
 |
 +--- FuncDeclStmt
 |
 +--- StaticVarDeclStmt


Expression
 |
 +--- ConstExpr                literales bool, int y float
 |
 +--- NewArrayExpr             Arreglos recien creados
 |
 +--- CallExpr                 Llamado a function
 |
 +--- VarExpr                  Variable en lado-derecho
 |
 +--- ArrayLoockupExpr         Contenido celda arreglo
 |
 +--- UnaryOpExpr              Unarios !, +, -
 |
 +--- BinaryOpExpr             Binarios ||,&&,==,!=,<,<=,>,>=,+,-,*,/,%
 |
 +--- VarAssignmentExpr        var = expr
 |
 +--- ArrayAssignmentExpr      var[expr] = expr
 |
 +--- IntToFloatExpr           Ensanchar integer a un float
 |
 +--- ArraySizeExpr            tamaño de un arreglo
'''
from dataclasses import dataclass, field
from multimethod import multimeta
from typing      import Union, List


# =====================================================================
# Clases Abstractas
# =====================================================================
@dataclass
class Visitor(metaclass=multimeta):
    '''
    Clase abstracta del Patron Visitor
    '''
    pass

@dataclass
class Node:
    def accept(self, v:Visitor, *args, **kwargs):
        return v.visit(self, *args, **kwargs)

@dataclass
class Statement(Node):
    pass

@dataclass
class Expression(Node):
    pass

@dataclass
class Declaration(Node):
    pass

# =====================================================================
# Clases Concretas
# =====================================================================

@dataclass
class Program(Expression):
    decls : List[Declaration] = field(default_factory=list)
    
@dataclass
class NullStmt(Statement):
    pass

@dataclass
class ForStmt(Statement):
    init: Statement
    cond: Expression
    iter: Statement
    stmt: Statement

@dataclass
class CastExpr(Expression):
    _type: str
    expr: Expression
    
@dataclass
class CompoundStmt(Statement):
    decls: List[Declaration] = field(default_factory=list)
    stmts: List[Statement] = field(default_factory=list)

@dataclass
class FuncDeclStmt(Statement):
    _type : str
    ident : str
    params : List[Expression] = field(default_factory=list)
    stmts : CompoundStmt = None

@dataclass
class ClassDeclStmt(Declaration):
    ident: str
    class_body: List[Declaration] = field(default_factory=list)

@dataclass
class VarDeclStmt(Statement):
    _type  : str
    ident : str

    @property
    def type(self):
        return self._type

@dataclass
class ArrayDeclStmt(Statement):
    _type  : str
    ident : str

    @property
    def type(self):
        return self.type

@dataclass
class WhileStmt(Statement):
    expr : Expression
    stmt : Statement

@dataclass
class IfStmt(Statement):
    expr : Expression
    then : Statement
    else_: Statement = None

@dataclass
class ReturnStmt(Statement):
    expr: Expression = None

@dataclass
class BreakStmt(Statement):
    pass

@dataclass
class ContinueStmt(Statement):
    pass

#===========================================================
#Expresiones
#===========================================================

@dataclass
class ConstExpr(Expression):
    value : Union[bool, int, float, str]
    
@dataclass
class NewArrayExpr(Expression):
    _type : str
    expr : Expression

    @property
    def type(self):
        return self.type
    
@dataclass
class VarExpr(Expression):
    ident: str
    
@dataclass
class ArrayLoockupExpr(Expression):
    ident : str
    expr  : Expression
    
@dataclass
class CallExpr(Expression):
    ident : str
    args : List[Expression] = field(default_factory=list)

@dataclass
class VarAssignmentExpr(Expression):
    var  : str
    expr : Expression
    
@dataclass
class ArrayAssignmentExpr(Expression):
    ident : str
    ndx   : Expression
    expr  : Expression
    
@dataclass
class BinaryOpExpr(Expression):
    opr   : str
    left  : Expression
    right : Expression    
    
@dataclass
class UnaryOpExpr(Expression):
    opr  : str
    expr : Expression

@dataclass
class SizeOfExpr(Expression):
    ident : str
    
@dataclass
class IntToFloatExpr(Expression):
    expr : Expression

@dataclass
class ArraySizeExpr(Expression):
    ident : str

@dataclass
class ExprStmt(Expression):
    expr : Expression
    
@dataclass
class PreInc(Expression):
    op     : str
    expr   : Expression

@dataclass
class PreDec(Expression):
    op     : str
    expr   : Expression
    
@dataclass
class PostInc(Expression):
    op     : str
    expr   : Expression

@dataclass
class PostDec(Expression):
    op     : str
    expr   : Expression

@dataclass
class OperatorAssign(Expression):
    op     : str
    expr0  : Expression
    expr1  : Expression
    
@dataclass
class PrintfStmt(Expression):
    string : str
    args   : List[Expression] = field(default_factory=list)

@dataclass
class ScanfStmt(Expression):
    string : str
    args   : List[Expression] = field(default_factory=list)
    
@dataclass
class Set(Expression):
    obj   : str
    name  : str
    expr  : Expression

@dataclass
class Get(Expression):
    obj   : str
    name  : str

@dataclass
class Super(Expression):
    name   : str
    
@dataclass
class This(Expression):
    pass

@dataclass
class Grouping(Expression):
    expr : Expression
    
@dataclass
class LogicalOpExpr(Expression):
    opr   : str
    left  : Expression
    right : Expression

@dataclass
class SprintfStmt(Expression):
    ident : str
    string : str
    args   : List[Expression] = field(default_factory=list)
        
#==========================================================
# Render del AST - RICH
#==========================================================

from rich.console import Console
from rich.tree import Tree

# Visitor para renderizar el AST
class RenderTreeVisitor(Visitor):
    def __init__(self):
        self.seq = 0
        
    def _seq(self):
        self.seq += 1
        return f"n{self.seq}"
    
    def visit(self, n: Program, parent_tree: Tree):
        prog_node = parent_tree.add(f'[bold cyan]Program[/bold cyan]')
        for decl in n.decls:
            decl.accept(self, prog_node)

    def visit(self, n: VarAssignmentExpr, parent_tree: Tree):
        var_node = parent_tree.add(f'[bold yellow]VarAssignment[/bold yellow]')
        var_node.add(f'var: {n.var}')
        n.expr.accept(self, var_node)
        
    def visit(self, n: VarDeclStmt, parent_tree: Tree):
        var_node = parent_tree.add(f'[bold green]VarDeclStmt[/bold green]')
        var_node.add(f'type: {n._type}')
        var_node.add(f'ident: {n.ident}')
        return var_node
        
    def visit(self, n: ArrayDeclStmt, parent_tree: Tree):
        Array = parent_tree.add(f'[bold green]ArrayDeclStmt[/bold green]')
        Array.add(f'type: {n._type}')
        Array.add(f'ident: {n.ident}')

    def visit(self, n: ExprStmt, parent_tree: Tree):
        expr_node = parent_tree.add(f'[bold magenta]ExprStmt[/bold magenta]')
        n.expr.accept(self, expr_node)
        
    def visit(self, n: IfStmt, parent_tree: Tree):
        if_node = parent_tree.add(f'[bold red]IfStmt[/bold red]')
        n.expr.accept(self, if_node)
        n.then.accept(self, if_node)
        if n.else_:
            n.else_.accept(self, if_node)

    def visit(self, n: WhileStmt, parent_tree: Tree):
        while_node = parent_tree.add(f'[bold red]WhileStmt[/bold red]')
        n.expr.accept(self, while_node)
        n.stmt.accept(self, while_node)

    def visit(self, n: ForStmt, parent_tree: Tree):
        for_node = parent_tree.add(f'[bold red]ForStmt[/bold red]')
        if isinstance(n.init, VarAssignmentExpr):
            for_node.add(f'init:{n.init.var} = {n.init.expr.value}')
            
        if isinstance(n.cond, BinaryOpExpr):
            for_node.add(f'cond:{n.cond.left.ident} {n.cond.opr} {n.cond.right.value}')
        
        if isinstance(n.iter, PostDec):
            for_node.add(f'iter:{n.iter.op} {n.iter.expr.ident}')
        if isinstance(n.iter, PostInc):
            for_node.add(f'iter:{n.iter.op} {n.iter.expr.ident}')
        if isinstance(n.iter, PreDec):
            for_node.add(f'iter:{n.iter.op} {n.iter.expr.ident}')
        if isinstance(n.iter, PreInc):
            for_node.add(f'iter:{n.iter.op} {n.iter.expr.ident}')
            
        n.stmt.accept(self, for_node)
    
    def visit(self, n: ReturnStmt, parent_tree: Tree):
        return_node = parent_tree.add('[bold blue]ReturnStmt[/bold blue]')
        if n.expr:
            n.expr.accept(self, return_node)
        
    def visit(self, n: BreakStmt, parent_tree: Tree):
        parent_tree.add(f'[bold blue]BreakStmt[/bold blue]')

    def visit(self, n: ContinueStmt, parent_tree: Tree):
        parent_tree.add(f'[bold blue]ContinueStmt[/bold blue]')

    def visit(self, n: FuncDeclStmt, parent_tree: Tree):
        func_node = parent_tree.add(f'[bold cyan]Function[/bold cyan]')
        func_node.add(f'type: {n._type}')
        func_node.add(f'ident: {n.ident}')
        if n.params != None:
            func_node.add(f'[bold cyan]Args: [bold cyan]')
            for param in n.params:
                func_node.add(f'Type: {param.type}')
                func_node.add(f'Ident: {param.ident}')
        n.stmts.accept(self, func_node)

    def visit(self, n: ConstExpr, parent_tree: Tree):
        Const_node = parent_tree.add(f'[bold yellow]ConstExpr[/bold yellow]')
        Const_node.add(f'Value: {n.value}')

    def visit(self, n: VarExpr, parent_tree: Tree):
        VarExpr = parent_tree.add(f'[bold yellow]VarExpr[/bold yellow]')
        VarExpr.add(f'Ident: {n.ident}')
        
    def visit(self, n: BinaryOpExpr, parent_tree: Tree):
        binary_node = parent_tree.add(f'[bold magenta]BinaryOp[/bold magenta]')
        binary_node.add(f'opr: {n.opr}')
        n.left.accept(self, binary_node)
        n.right.accept(self, binary_node)
        
    def visit(self, n: UnaryOpExpr, parent_tree: Tree):
        unary_node = parent_tree.add(f'[bold magenta]UnaryOp[/bold magenta]')
        unary_node.add(f'opr: {n.opr}')
        n.expr.accept(self, unary_node)
        
    def visit(self, n: CallExpr, parent_tree: Tree):
        call_node = parent_tree.add(f'[bold yellow]CallExpr[/bold yellow]')
        call_node.add(f'Ident: {n.ident}')
        call_node.add(f'Args:')
        if n.args != None:
            for arg in n.args:
                arg.accept(self, call_node)
            
    def visit(self, n: NewArrayExpr, parent_tree: Tree):
        array_node = parent_tree.add(f'[bold green]New Array[/bold green]') 
        array_node.add(f'type: {n._type}')
        array_node.add(f'expr: {n.expr}')
        n.size_expr.accept(self, array_node)
            
    def visit(self, n: NullStmt, parent_tree: Tree):
        parent_tree.add(f'[bold blue]NullStmt[/bold blue]')
    
    def visit(self, n: IntToFloatExpr, parent_tree: Tree):
        cast_node = parent_tree.add(f'[bold magenta]IntToFloat[/bold magenta]')
        cast_node.add(f'expr: {n.expr}')
        n.expr.accept(self, cast_node)
        
    def visit(self, n: CompoundStmt, parent_tree: Tree):
        compound_node = parent_tree.add("[bold cyan]CompoundStmt[/bold cyan]")
        
        for local_decl in n.decls:
            local_decl.accept(self, compound_node)

        for stmt in n.stmts:
            stmt.accept(self, compound_node)
            
    def visit(self, n: ArraySizeExpr, parent_tree: Tree):
        size_node = parent_tree.add(f'[bold yellow]ArraySizeExpr[/bold yellow]')
        size_node.add(f'Ident: {n.ident}')
        n.ident.accept(self, size_node)
    
    def visit(self, n: SizeOfExpr, parent_tree: Tree):
        size_node = parent_tree.add(f'[bold yellow]SizeOfExpr[/bold yellow]')
        size_node.add(f'Ident: {n.ident}')
        n.ident.accept(self, size_node)
    
    def visit(self, n: ArrayAssignmentExpr, parent_tree: Tree):
        ArrayAssign_node = parent_tree.add(f'[bold yellow]ArrayAssignmentExpr[/bold yellow]')
        ArrayAssign_node.add(f'Ident: {n.ident}')
        ArrayAssign_node.add(f'Ndx: {n.ndx}')
        ArrayAssign_node.add(f'Expr: {n.expr}')
        n.ndx.accept(self, ArrayAssign_node)
        n.expr.accept(self, ArrayAssign_node)
        n.ident.accept(self, ArrayAssign_node)
        
    def visit(self, n: ClassDeclStmt, parent_tree: Tree):
        Class_node = parent_tree.add(f'[bold blue]ClassDeclStmt[/bold blue]')
        Class_node.add(f'Ident: {n.ident}')
        for decl in n.class_body:
            decl.accept(self, Class_node)
            
    def visit(self, n: CastExpr, parent_tree: Tree):
        Cast_node = parent_tree.add(f'[bold yellow]CastExpr[/bold yellow]')
        Cast_node.add(f'Type: {n._type}')
        Cast_node.add(f'Expr: {n.expr}')
        n.expr.accept(self, Cast_node)
    
    def visit(self, n: PostDec, parent_tree: Tree):
        Operator_node = parent_tree.add(f'[bold yellow]OperatorPostfix[/bold yellow]')
        Operator_node.add(f'Op: {n.op}')
        if isinstance(n.expr, ConstExpr):
            n.expr.accept(self, Operator_node)
        if isinstance(n.expr, VarExpr):
            n.expr.accept(self, Operator_node)
    
    def visit(self, n: PostInc, parent_tree: Tree):
        Operator_node = parent_tree.add(f'[bold yellow]OperatorPostfix[/bold yellow]')
        Operator_node.add(f'Op: {n.op}')
        if isinstance(n.expr, ConstExpr):
            n.expr.accept(self, Operator_node)
        if isinstance(n.expr, VarExpr):
            n.expr.accept(self, Operator_node)
    
    def visit(self, n: PreDec, parent_tree: Tree):
        Operator_node = parent_tree.add(f'[bold yellow]OperatorPrefix[/bold yellow]')
        Operator_node.add(f'Op: {n.op}')
        if isinstance(n.expr, ConstExpr):
            n.expr.accept(self, Operator_node)
        if isinstance(n.expr, VarExpr):
            n.expr.accept(self, Operator_node)
    
    def visit(self, n: PreInc, parent_tree: Tree):
        Operator_node = parent_tree.add(f'[bold yellow]OperatorPrefix[/bold yellow]')
        Operator_node.add(f'Op: {n.op}')
        if isinstance(n.expr, ConstExpr):
            n.expr.accept(self, Operator_node)
        if isinstance(n.expr, VarExpr):
            n.expr.accept(self, Operator_node)
    
    def visit(self, n: OperatorAssign, parent_tree: Tree):
        Operator_node = parent_tree.add(f'[bold yellow]OperatorAssign[/bold yellow]')
        Operator_node.add(f'Op: {n.op}')
        if isinstance(n.expr0, ConstExpr):
            n.expr0.accept(self, Operator_node)
        if isinstance(n.expr1, ConstExpr):
            n.expr1.accept(self, Operator_node)
    
    def visit(self, n: PrintfStmt, parent_tree: Tree):
        Printf_node = parent_tree.add(f'[bold yellow]PrintfStmt[/bold yellow]')
        Printf_node.add(f'String: {n.string}')
        for arg in n.args:
            arg.accept(self, Printf_node)
    
    def visit(self, n: ScanfStmt, parent_tree: Tree):
        Scanf_node = parent_tree.add(f'[bold yellow]ScanfStmt[/bold yellow]')
        Scanf_node.add(f'String: {n.string}')
        for arg in n.args:
            arg.accept(self, Scanf_node)
        
    def visit(self, n: Set, parent_tree: Tree):
        Set_node = parent_tree.add(f'[bold yellow]Set[/bold yellow]')
        Set_node.add(f'Obj: {n.obj}')
        Set_node.add(f'Name: {n.name}')
        Set_node.add(f'Expr: {n.expr}')
        n.expr.accept(self, Set_node)
    
    def visit(self, n: Get, parent_tree: Tree):
        Get_node = parent_tree.add(f'[bold yellow]Get[/bold yellow]')
        Get_node.add(f'Obj: {n.obj}')
        Get_node.add(f'Name: {n.name}')
    
    def visit(self, n: Super, parent_tree: Tree):
        Super_node = parent_tree.add(f'[bold yellow]Super[/bold yellow]')
        Super_node.add(f'Name: {n.name}')
    
    def visit(self, n: This, parent_tree: Tree):
        This_node = parent_tree.add(f'[bold yellow]This[/bold yellow]')
        
    def visit(self, n: Grouping, parent_tree: Tree):
        Grouping_node = parent_tree.add(f'[bold yellow]Grouping[/bold yellow]')
        n.expr.accept(self, Grouping_node)
    
    def visit(self, n: LogicalOpExpr, parent_tree: Tree):
        Logical_node = parent_tree.add(f'[bold yellow]LogicalOpExpr[/bold yellow]')
        Logical_node.add(f'Opr: {n.opr}')
        n.left.accept(self, Logical_node)
        n.right.accept(self, Logical_node)
        
    def visit(self, n: SprintfStmt, parent_tree: Tree):
        Sprintf_node = parent_tree.add(f'[bold yellow]SprintfStmt[/bold yellow]')
        Sprintf_node.add(f'Ident: {n.ident}')
        Sprintf_node.add(f'String: {n.string}')
        for arg in n.args:
            arg.accept(self, Sprintf_node)
            
        
            
# =====================================================================
# Función para renderizar el AST
# =====================================================================

    def render(self, root_node):
            tree = Tree("AST")
            self.visit(root_node, tree)
            console = Console()
            console.print(tree)
