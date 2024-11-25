from collections import ChainMap  # Tabla de Simbolos
from typing import Union
from MiniCppAST import *
from MiniCpptypesys import *
from tabulate import tabulate

class CheckError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        self.env = ChainMap()

    def push_scope(self):
        # Añadir un nuevo alcance.
        self.env = self.env.new_child()

    def pop_scope(self):
        # Eliminar el alcance actual.
        self.env = self.env.parents

    def define(self, name, value):
        # Definir un símbolo en el alcance actual.
        self.env[name] = value

    def lookup(self, name):
        # Buscar un símbolo en la tabla de símbolos.
        for n, e in enumerate(self.env.maps):
            if name in e:
                if not e[name]:
                    raise CheckError("No se puede hacer referencia a una variable en su propia inicialización")
                return e[name]
        raise CheckError(f"'{name}' no está definido")

    def get_symbol_table(self):
        print("Tabla de símbolos:\n")
        for i, scope in enumerate(self.env.maps):
            print(f'Nivel de alcance {i}:')
            table = [[k, type(v).__name__] for k, v in scope.items()]
            print(tabulate(table, headers=["Variable", "Tipo"], tablefmt="grid"), "\n")
        print()

class Checker(Visitor):

    @classmethod
    def check(cls, n: Node, env: SymbolTable):
        checker = cls()
        n.accept(checker,SymbolTable())
        return checker

    def visit(self, n: Program, env: SymbolTable):
        env.define('scanf', True)
        env.define('printf', True)
        for decl in n.decls:
            decl.accept(self, env)
        if not env.lookup('main'):
            raise CheckError("No se encontró la función 'main'")

    def visit(self, n: FuncDeclStmt, env: SymbolTable):
        '''
        1. Guardar la función en la TS
        2. Crear una TS para la función
        3. Agregar n.params dentro de la TS
        4. Visitar n.body
        '''
        env.define(n.ident, n)
        env.push_scope()
        env.define('fun', True)
        if n.params is not None:
            for p in n.params:
                env.define(p.ident, p)
        n.stmts.accept(self, env)
    
    def visit(self, n: ClassDeclStmt, env: SymbolTable):
        env.define(n.ident, n)
        env.push_scope()
        for decl in n.decls:
            decl.accept(self, env)

    def visit(self, n: VarDeclStmt, env: SymbolTable):
        '''
        1. Agregar n.ident a la TS actual
        '''
        env.define(n.ident, n)

    # Statements

    def visit(self, n: CompoundStmt, env: SymbolTable):
        '''
        1. Crear una tabla de simbolos
        2. Visitar Declaration/Statement
        '''
        for decl in n.decls:
            decl.accept(self, env)
        for stmt in n.stmts:
            stmt.accept(self, env)

    def visit(self, n: IfStmt, env: SymbolTable):
        '''
        1. Visitar n.expr (validar tipos)
        2. Visitar Statement por n.then
        3. Si existe opcion n.else_, visitar
        '''
        n.expr.accept(self, env)
        n.then.accept(self, env)
        if n.else_:
            n.else_.accept(self, env)

    def visit(self, n: WhileStmt, env: SymbolTable):
        '''
        1. Visitar n.expr (validar tipos)
        2. visitar n.stmt
        '''
        env.define('while', True)
        n.expr.accept(self, env)
        n.stmt.accept(self, env)
        env.define('while', False)

    def visit(self, n: ForStmt, env: SymbolTable):
        '''
        1. Visitar n.init, n.cond, n.iter y n.stmt
        '''
        env.define('for', True)
        n.init.accept(self, env)
        n.cond.accept(self, env)
        n.iter.accept(self, env)
        n.stmt.accept(self, env)
        env.define('for', False)

    def visit(self, n: BreakStmt, env: SymbolTable):
        '''
        1. Verificar que esta dentro de un ciclo while/for
        '''
        if 'while' not in env.env and 'for' not in env.env:
            raise CheckError('break usado fuera de un while/for')

    def visit(self, n: ContinueStmt, env: SymbolTable):
        '''
        1. Verificar que esta dentro de un ciclo while/for
        '''
        if 'while' not in env.env and 'for' not in env.env:
            raise CheckError('continue usado fuera de un while/for')

    def visit(self, n: ReturnStmt, env: SymbolTable):
        '''
        1. Si se ha definido n.expr, validar que sea del mismo tipo de la función
        '''
        if n.expr:
            n.expr.accept(self, env)
            if 'fun' not in env.env:
                raise CheckError('return usado fuera de una funcion')

    def visit(self, n: ExprStmt, env: SymbolTable):
        n.expr.accept(self, env)

    # Expressions

    def visit(self, n: ConstExpr, env: SymbolTable):
        pass

    def visit(self, n: BinaryOpExpr, env: SymbolTable):
        n.left.accept(self, env)
        n.right.accept(self, env)
        expr_type_left = self.resolve_type(n.left, env)
        expr_type_right = self.resolve_type(n.right, env)
        if expr_type_left != expr_type_right:
            raise CheckError(f"tipos incompatibles: {n.left} {expr_type_left} = {expr_type_right} {n.right}")
        
        result_type = check_binary_op(n.opr, expr_type_left, expr_type_right)
        if result_type is None:
            raise CheckError(f"Operación binaria no soportada: {n.opr} entre {expr_type_left} y {expr_type_right}")
        n.type = result_type

    def visit(self, n: UnaryOpExpr, env: SymbolTable):
        n.expr.accept(self, env)
        expr_type = self.resolve_type(n.expr, env)
        result_type = check_unary_op(n.opr, expr_type)
        if result_type is None:
            raise CheckError(f"Operación unaria no soportada: {n.opr} para {expr_type}")
        n.type = result_type

    def visit(self, n: VarExpr, env: SymbolTable):
        try:
            var = env.lookup(n.ident)
        except CheckError as err:
            raise CheckError(str(err))
        n.type = var._type if hasattr(var, '_type') else type(var).__name__

    def visit(self, n: VarAssignmentExpr, env: SymbolTable):
        n.expr.accept(self, env)
        try:
            var = env.lookup(n.var)
        except CheckError as err:
            raise CheckError(str(err))
        var_type = var._type if hasattr(var, '_type') else type(var).__name__
        expr_type = n.expr
        if isinstance(expr_type, ConstExpr):
            expr_type = type(n.expr.value).__name__
        else:
            expr_type = n.expr.type
        
        if isinstance(var, VarDeclStmt):
            var_type = var._type
        if isinstance(n.expr, VarExpr):
            expr_type = env.lookup(n.expr.ident)._type if hasattr(env.lookup(n.expr.ident), '_type') else type(env.lookup(n.expr.ident)).__name__
        
        if var_type != expr_type:
            raise CheckError(f"Asignación de tipos incompatibles: {var_type} = {expr_type}")
        n.type = var_type

    def visit(self, n: CastExpr, env: SymbolTable):
        n.expr.accept(self, env)
        if n._type not in typenames:
            raise CheckError(f"Tipo de cast no soportado: {n._type}")
        n.type = n._type
        
    def visit(self, n: CallExpr, env: SymbolTable):
        '''
        1. Verificar que la función llamada está definida
        2. Verificar los tipos de los argumentos
        '''
        try:
            func = env.lookup(n.ident)
        except CheckError as err:
            raise CheckError(str(err))
        
        if not isinstance(func, FuncDeclStmt):
            raise CheckError(f"{n.func} no es una función")
        
        if n.args is None:
            n.args = []
        
        if func.params is None:
            func.params = []
            
        if len(n.args) != len(func.params):
            raise CheckError(f"Número incorrecto de argumentos para la función {n.func}")
        
        for arg, param in zip(n.args, func.params):
            arg.accept(self, env)
            arg_type = self.resolve_type(arg, env)
            param_type = param._type
            if arg_type != param_type:
                raise CheckError(f"Tipo incorrecto para el argumento {arg}: se esperaba {param_type} pero se obtuvo {arg_type}")
        
        n.type = func._type
    
    def visit(self, n: Grouping, env: SymbolTable):
        n.expr.accept(self, env)
        n.type = n.expr.type
        
    def visit(self, n: Get, env: SymbolTable):
        self.visit(n.obj, env)
        Name = env.lookup(n.name)
        if Name is None:
            self.error(n, f"Checker error. Get symbol '{n.name}' is not defined")

    def visit(self, n: Set, env: SymbolTable):
        self.visit(n.obj, env)
        name= env.lookup(n.name)

        if name is None:
            self.error(n, f"Checker error. Set symbol '{n.name}' is not defined")

    def visit(self, n: This, env: SymbolTable):
        pass

    def visit(self, n: Super, env: SymbolTable):
        pass
    
    def visit(self, n: PrintfStmt, env: SymbolTable):
        pass
    
    def visit(self, n: ScanfStmt, env: SymbolTable):
        pass
    
    def visit(self, n: SprintfStmt, env: SymbolTable):
        pass
    
    def visit(self, n: NewArrayExpr, env: SymbolTable):
        pass
    
    def visit(self, n: PostInc, env: SymbolTable):
        pass
    
    def visit(self, n: PostDec, env: SymbolTable):
        pass
    
    def visit(self, n: PreInc, env: SymbolTable):
        pass
    
    def visit(self, n: PreDec, env: SymbolTable):
        pass
    
    def visit(self, n: OperatorAssign, env: SymbolTable):
        pass

    def resolve_type(self, expr, env):
        if isinstance(expr, BinaryOpExpr):
            return self.resolve_type(expr.left, env)
        if isinstance(expr, VarExpr):
            var = env.lookup(expr.ident)
            return var._type if hasattr(var, '_type') else type(var).__name__
        if isinstance(expr, ConstExpr):
            return type(expr.value).__name__
        if isinstance(expr, VarDeclStmt):
            return expr._type
        if isinstance(expr, Grouping):
            return self.resolve_type(expr.expr, env)
        
    def raise_error(self, msg, node):
        raise CheckError(f"{msg} en la línea {node.line}")

    def print_table(self, ast: Node):
        env = SymbolTable()
        self.visit(ast, env)
        print(env.get_symbol_table())