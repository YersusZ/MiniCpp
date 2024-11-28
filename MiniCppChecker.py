from collections import ChainMap  # Tabla de Simbolos
from typing import Union
from MiniCppAST import *
from MiniCpptypesys import *
from tabulate import tabulate
from rich.console import Console



class CheckError(Exception):
    def __init__(self, message):
        console = Console()
        # Renderiza el mensaje con estilo (en rojo, negrita)
        self.message = f"[bold red]{message}[/bold red]"
        # Almacena el mensaje como texto sin formato para el sistema de excepciones
        super().__init__(console.render_str(self.message))

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
                    return False
                return e[name]
        return False
    
    def lookup_func(self, name):
        # Buscar una función en la tabla de símbolos.
        for n, e in enumerate(self.env.maps):
            if name in e:
                if isinstance(e[name], FuncDeclStmt):
                    return True
        return False
    
    def lookup_class(self, name):
        # Buscar una clase en la tabla de símbolos.
        for n, e in enumerate(self.env.maps):
            if name in e:
                if isinstance(e[name], ClassDeclStmt):
                    return True
        return False

    def get_symbol_table(self):
        print("Tabla de símbolos:\n")
        for i, scope in enumerate(self.env.maps):
            table = [[k, type(v).__name__] for k, v in scope.items()]
            print(tabulate(table, headers=["Variable", "Tipo"], tablefmt="grid"), "\n")
        print()

class Checker(Visitor):

    @classmethod
    def check(cls, n: Node, env: SymbolTable):
        checker = cls()
        n.accept(checker,SymbolTable())
        return checker

    #==================================================================================================================
    
    def visit(self, n: Program, env: SymbolTable):
        env.define('scanf', True)
        env.define('printf', True)
        for decl in n.decls:
            decl.accept(self, env)
        if not env.lookup('main'):
            try:
                raise CheckError("No se encontró la función 'main'.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
    
    #==================================================================================================================

    def visit(self, n: FuncDeclStmt, env: SymbolTable):
        '''
        1. Guardar la función en la TS
        2. Crear una TS para la función
        3. Agregar n.params dentro de la TS
        4. Visitar n.body
        '''
        if env.lookup_func(n.ident):
            try:
                raise CheckError(f"Función '{n.ident}' ya definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        env.define(n.ident, n)
        env.push_scope()
        env.define('fun', True)
        if n.params is not None:
            for p in n.params:
                env.define(p.ident, p)
        self.type_func = n._type
        n.stmts.accept(self, env)
        if not env.lookup('return') and self.type_func != 'void':
            try:
                raise CheckError("Función sin retorno.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        if n._type == 'void' and env.lookup('return'):
            try:
                raise CheckError('Función con retorno en tipo void.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        env.pop_scope()
    
    #==================================================================================================================
        
    def visit(self, n: ReturnStmt, env: SymbolTable):
        if env.lookup('fun') is None:
            try:
                raise CheckError('return usado fuera de una función.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if n.expr == 'True' or n.expr == 'False':
            n.expr = bool
        if self.type_func != 'void':
            return_type = self.resolve_type(n.expr, env)
            if self.type_func != return_type:
                try:
                    raise CheckError(f"Tipo de retorno incorrecto: se esperaba '{self.type_func}' pero se obtuvo '{return_type}'.")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
    
    #==================================================================================================================
    
    
    def visit(self, n: ClassDeclStmt, env: SymbolTable):
        if env.lookup_class(n.ident):
            try:
                raise CheckError(f"Clase '{n.ident}' ya definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if n.sclass != None:
            if not env.lookup_class(n.sclass):
                try:
                    raise CheckError(f"Clase base '{n.sclass}' no definida.")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        env.define(n.ident, n)
        env.push_scope()
        for atribmethods in n.class_body:
            atribmethods.accept(self, env)
        env.pop_scope()
    
    #==================================================================================================================

    def visit(self, n: VarDeclStmt, env: SymbolTable):
        '''
        1. Agregar n.ident a la TS actual
        '''
        if env.lookup(n.ident):
            try:
                raise CheckError(f"Variable '{n.ident}' ya definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        env.define(n.ident, n)

    #==================================================================================================================

    # Statements

    def visit(self, n: CompoundStmt, env: SymbolTable):
        '''
        1. Crear una tabla de simbolos
        2. Visitar Declaration/Statement
        '''
        there_is_return = False
        for decl in n.decls:
            decl.accept(self, env)
        for stmt in n.stmts:
            if isinstance(stmt, ReturnStmt):
                there_is_return = True
            stmt.accept(self, env)
        if there_is_return:
            env.define('return', True)
        
    #==================================================================================================================

    def visit(self, n: IfStmt, env: SymbolTable):
        '''
        1. Visitar n.expr (validar tipos)
        2. Visitar Statement por n.then
        3. Si existe opcion n.else_, visitar
        '''
        if isinstance(n.expr, BinaryOpExpr):
            if (n.expr.opr != '<' and n.expr.opr != '>' and n.expr.opr != '<=' and n.expr.opr != '>=' and n.expr.opr != '=='):
                try:
                    raise CheckError('La condición del if debe ser una comparación.')
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        else:
            typecond = self.resolve_type(n.expr, env)
            if typecond != 'bool':
                try:
                    raise CheckError('La condición del if debe ser una expresión booleana.')
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
            
        n.expr.accept(self, env)
        n.then.accept(self, env)
        if n.else_:
            n.else_.accept(self, env)
            
    #==================================================================================================================        

    def visit(self, n: WhileStmt, env: SymbolTable):
        '''
        1. Visitar n.expr (validar tipos)
        2. visitar n.stmt
        '''
        if isinstance(n.expr, BinaryOpExpr):
            if (n.expr.opr != '<' and n.expr.opr != '>' and n.expr.opr != '<=' and n.expr.opr != '>=' and n.expr.opr != '=='):
                try:
                    raise CheckError('La condición del ciclo while debe ser una comparación.')
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        else:
            typecond = self.resolve_type(n.expr, env)
            if typecond != 'bool': 
                try:
                    raise CheckError('La condición del ciclo while debe ser una expresión binaria.')
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
            
        env.define('while', True)
        n.expr.accept(self, env)
        n.stmt.accept(self, env)
        env.define('while', False)
    
    #==================================================================================================================

    def visit(self, n: ForStmt, env: SymbolTable):
        '''
        1. Visitar n.init, n.cond, n.iter y n.stmt
        '''
        if not isinstance(n.init, (VarAssignmentExpr, VarDeclStmt)):
            try:
                raise CheckError('La inicialización del ciclo for debe ser una asignación.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        if isinstance(n.cond, BinaryOpExpr):
            if n.cond.opr != '<' and n.cond.opr != '>' and n.cond.opr != '<=' and n.cond.opr != '>=':
                try:
                    raise CheckError('La condición del ciclo for debe ser una comparación.') 
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        else:
            try:
                raise CheckError('La condición del ciclo for debe ser una expresión binaria.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        if not isinstance(n.iter, (PostDec, PreDec, PostInc, PreInc)):
            try:
                raise CheckError('Debe ser un incremento/decremento.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        env.define('for', True)
        n.init.accept(self, env)
        n.cond.accept(self, env)
        n.iter.accept(self, env)
        n.stmt.accept(self, env)
        env.define('for', False)
        
    #==================================================================================================================

    def visit(self, n: BreakStmt, env: SymbolTable):
        '''
        1. Verificar que esta dentro de un ciclo while/for
        '''
        if not env.lookup('while') and not env.lookup('for'):
            try:
                raise CheckError('break usado fuera de un while/for.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
            
    #==================================================================================================================

    def visit(self, n: ContinueStmt, env: SymbolTable):
        '''
        1. Verificar que esta dentro de un ciclo while/for
        '''
        if not env.lookup('while') and not env.lookup('for'):
            try:
                raise CheckError('continue usado fuera de un while/for.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
    
    #==================================================================================================================

    #Expressions
    
    def visit(self, n: ExprStmt, env: SymbolTable):
        n.expr.accept(self, env)
        
    #==================================================================================================================
    
    def visit(self, n: ConstExpr, env: SymbolTable):
        pass
    
    #==================================================================================================================
    
    def visit(self, n: BinaryOpExpr, env: SymbolTable):
        n.left.accept(self, env)
        n.right.accept(self, env)
        expr_type_left = self.resolve_type(n.left, env)
        expr_type_right = self.resolve_type(n.right, env)
        if expr_type_left != expr_type_right:
            try:
                raise CheckError(f"tipos incompatibles: {n.left} {expr_type_left} = {expr_type_right} {n.right}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        result_type = check_binary_op(n.opr, expr_type_left, expr_type_right)
        if result_type is None:
            try:
                raise CheckError(f"Operación binaria no soportada: {n.opr} entre {expr_type_left} y {expr_type_right}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = result_type
        
    #==================================================================================================================
    
    def visit(self, n: UnaryOpExpr, env: SymbolTable):
        n.expr.accept(self, env)
        expr_type = self.resolve_type(n.expr, env)
        result_type = check_unary_op(n.opr, expr_type)
        if result_type is None:
            try:
                raise CheckError(f"Operación unaria no soportada: {n.opr} para {expr_type}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = result_type
    
    #==================================================================================================================

    def visit(self, n: VarExpr, env: SymbolTable):
        var = env.lookup(n.ident)
        if not var:
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = var._type if hasattr(var, '_type') else type(var).__name__
    
    #==================================================================================================================

    def visit(self, n: VarAssignmentExpr, env: SymbolTable):
        n.expr.accept(self, env)
        var = env.lookup(n.var)
        if not var:
            try:
                raise CheckError(f"Variable '{n.var}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        var_type = var._type if hasattr(var, '_type') else type(var).__name__
        expr_type = self.resolve_type(n.expr, env)
        
        if var_type != expr_type:
            try:
                raise CheckError(f"Asignación de tipos incompatibles: {var_type} = {expr_type}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = var_type
    
    #==================================================================================================================
        
    def visit(self, n: ArrayDeclStmt, env: SymbolTable):
        array = env.lookup(n.ident)
        if array:
            try:
                raise CheckError(f"Variable '{n.ident}' ya definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        env.define(n.ident, n)
    
    #==================================================================================================================
    
    def visit(self, n: ArrayAssignmentExpr, env: SymbolTable):
        n.expr.accept(self, env)
        array = env.lookup(n.ident)
        if not array:
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if self.resolve_type(n.ndx, env) != 'int':
            try:
                raise CheckError(f"Índice de arreglo debe ser un entero.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if array._type != self.resolve_type(n.expr, env):
            try:
                raise CheckError(f"Tipo de arreglo incompatible: {array._type} = {self.resolve_type(n.expr, env)}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = array._type
    
    #==================================================================================================================

    def visit(self, n: CastExpr, env: SymbolTable):
        n.expr.accept(self, env)
        if not isinstance(n.expr, VarExpr):
            try:
                raise CheckError(f"Cast no soportado: {n.expr}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if n.expr.type == n._type:
            try:
                raise CheckError(f"Cast innecesario: {n.expr.type} a {n._type}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if n._type not in typenames:
            try:
                raise CheckError(f"Tipo de cast no soportado: {n._type}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = n._type
    
    #==================================================================================================================
        
    def visit(self, n: CallExpr, env: SymbolTable):
        '''
        1. Verificar que la función llamada está definida
        2. Verificar los tipos de los argumentos
        '''
        func = env.lookup(n.ident)
        if not func:
            try:
                raise CheckError(f"Función '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if not isinstance(func, FuncDeclStmt):
            try:
                raise CheckError(f"{n.ident} no es una función")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        if n.args is None:
            n.args = []
        
        if func.params is None:
            func.params = []
            
        if len(n.args) != len(func.params):
            try:
                raise CheckError(f"Número incorrecto de argumentos para la función {n.ident}: se esperaban {len(func.params)} pero se obtuvieron {len(n.args)}")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        for arg, param in zip(n.args, func.params):
            arg.accept(self, env)
            arg_type = self.resolve_type(arg, env)
            param_type = param._type
            if arg_type != param_type:
                try:
                    raise CheckError(f"Tipo incorrecto para el argumento {arg}: se esperaba {param_type} pero se obtuvo {arg_type}")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        
        n.type = func._type
    
    #==================================================================================================================
    
    def visit(self, n: Grouping, env: SymbolTable):
        n.expr.accept(self, env)
        n.type = n.expr.type
    
    #==================================================================================================================
        
    def visit(self, n: Get, env: SymbolTable):
        self.visit(n.obj, env)
        Name = env.lookup(n.name)
        if not Name:
            try:
                raise CheckError(f"El atributo '{n.name}' no esta definido.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
            
    #==================================================================================================================
    
    def visit(self, n: Set, env: SymbolTable):
        self.visit(n.obj, env)
        Name = env.lookup(n.name)
        if not Name:
            try:
                raise CheckError(f"El atributo '{n.name}' no esta definido.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
            
    #==================================================================================================================
        
    def visit(self, n: ArrayLoockupExpr, env: SymbolTable):
        if not env.lookup(n.ident):
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
        if self.resolve_type(n.expr, env) != 'int':
            try:
                raise CheckError(f"Índice de arreglo debe ser un entero.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = n.ident
    
    #==================================================================================================================
    
    def visit(self, n: SizeOfExpr, env: SymbolTable):
        size = env.lookup(n.ident)
        if not size:
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        else:
            size = self.resolve_type(size, env)
            n.type = size
            
    #==================================================================================================================
        
    def visit(self, n: IntToFloatExpr, env: SymbolTable):
        n.expr.accept(self, env)
        if self.resolve_type(n.expr, env) != 'int':
            try:
                raise CheckError(f"IntToFloat solo acepta enteros.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = 'float'
        
    #==================================================================================================================
    
    def visit(self, n: ArraySizeExpr, env: SymbolTable):
        Array = env.lookup(n.ident)
        if not Array:
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        if not isinstance(Array, ArrayDeclStmt):
            try:
                raise CheckError(f"Variable '{n.ident}' no es un arreglo.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
    
    #==================================================================================================================
                
    def visit(self, n:ExprStmt, env: SymbolTable):
        n.expr.accept(self, env)
        
    #==================================================================================================================
        
    def visit(self, n: This, env: SymbolTable):
        pass
    
    #==================================================================================================================
    
    def visit(self, n: Super, env: SymbolTable):
        pass
    
    #==================================================================================================================
    
    def visit(self, n: PrintfStmt, env: SymbolTable):
        if not isinstance(n.string, str):
            try:
                raise CheckError('La cadena de formato debe ser una cadena.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        format_specifiers = self.get_format_specifiers(n.string)
        if len(format_specifiers) != len(n.args):
            try:
                raise CheckError('Número incorrecto de argumentos para la función printf.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
                
        for arg, specifier in zip(n.args, format_specifiers):
            arg_type = self.resolve_type(arg, env)
            if arg_type != specifier:
                try:
                    raise CheckError(f"Tipo incorrecto para el argumento {arg}: se esperaba {specifier} pero se obtuvo {arg_type}")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
                    
        for arg in n.args:
            arg.accept(self, env)
    
    #==================================================================================================================
    
    def visit(self, n: ScanfStmt, env: SymbolTable):
        if not isinstance(n.string, str):
            try:
                raise CheckError('La cadena de formato debe ser una cadena.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
                
        format_specifiers = self.get_format_specifiers(n.string)
        
        if len(format_specifiers) != len(n.args):
            try:
                raise CheckError('Número incorrecto de argumentos para la función scanf.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
                
        for arg, specifier in zip(n.args, format_specifiers):
            arg_type = self.resolve_type(arg, env)
            if arg_type != specifier:
                try:
                    raise CheckError(f"Tipo incorrecto para el argumento {arg}: se esperaba {specifier} pero se obtuvo {arg_type}")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        
        for arg in n.args:
            arg.accept(self, env)
        
        
    #==================================================================================================================
    
    def visit(self, n: NewArrayExpr, env: SymbolTable):
        if n._type not in typenames:
            try:
                raise CheckError(f"Tipo de arreglo no soportado: {n._type}")
            except CheckError as err:
                console = Console()
                console.print(err.message)
    
    #==================================================================================================================
    
    def visit(self, n: PostInc, env: SymbolTable):
        if not isinstance(n.expr, VarExpr):
            try:
                raise CheckError('Incremento solo acepta variables.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
    
    #==================================================================================================================
    
    def visit(self, n: PostDec, env: SymbolTable):
        if not isinstance(n.expr, VarExpr):
            try:
                raise CheckError('Decremento solo acepta variables.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
        
    #==================================================================================================================
    
    def visit(self, n: PreInc, env: SymbolTable):
        if not isinstance(n.expr, VarExpr):
            try:
                raise CheckError('Incremento solo acepta variables.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
    
    #==================================================================================================================
    
    def visit(self, n: PreDec, env: SymbolTable):
        if not isinstance(n.expr, VarExpr):
            try:
                raise CheckError('Decremento solo acepta variables.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr.accept(self, env)
        
    #==================================================================================================================
    
    def visit(self, n: OperatorAssign, env: SymbolTable):
        if not isinstance(n.expr0, VarExpr):
            try:
                raise CheckError('Operador de asignación solo acepta variables.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.expr0.accept(self, env)
        n.expr1.accept(self, env)
        
    #==================================================================================================================
        
    def visit(self, n: NullStmt, env: SymbolTable):
        pass
    
    #==================================================================================================================
    
    def visit(self, n: LogicalOpExpr, env: SymbolTable):
        n.left.accept(self, env)
        n.right.accept(self, env)
        if n.left.type != 'bool' or n.right.type != 'bool':
            try:
                raise CheckError(f"Operación lógica no soportada: {n.left.type} {n.opr} {n.right.type}.")
            except CheckError as err:
                console = Console()
                console.print(err.message)

        if n.opr != '&&' and n.opr != '||':
            try:
                raise CheckError(f"Operador lógico no soportado: {n.opr}")
            except CheckError as err:
                console = Console()
                console.print(err.message)
        n.type = 'bool'

    #==================================================================================================================
    
    def visit(self, n: SprintfStmt, env: SymbolTable):
        char = env.lookup(n.ident)
        if not char:
            try:
                raise CheckError(f"Variable '{n.ident}' no definida.")
            except CheckError as err:
                console = Console()
                console.print(err.message)
                
        if char._type != 'char':
            try:
                raise CheckError(f"Variable '{n.ident}' no es un char.")
            except CheckError as err:
                console = Console()
                console.print(err.message) 
                
        if not isinstance(n.string, str):
            try:
                raise CheckError('La cadena de formato debe ser una cadena.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        if len(n.args) != len(self.get_format_specifiers(n.string)):
            try:
                raise CheckError('Número incorrecto de argumentos para la función sprintf.')
            except CheckError as err:
                console = Console()
                console.print(err.message)
        
        format_specifiers = self.get_format_specifiers(n.string)
        for arg, specifier in zip(n.args, format_specifiers):
            arg_type = self.resolve_type(arg, env)
            if arg_type != specifier:
                try:
                    raise CheckError(f"Tipo incorrecto para el argumento {arg}: se esperaba {specifier} pero se obtuvo {arg_type}")
                except CheckError as err:
                    console = Console()
                    console.print(err.message)
        
    #==================================================================================================================
    #Metodos auxiliares

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
        if isinstance(expr, VarAssignmentExpr):
            return self.resolve_type(expr.expr, env)
        if isinstance(expr, CallExpr):
            return expr.type
        if isinstance(expr, LogicalOpExpr):
            return 'bool'
    
    def get_format_specifiers(self, string):
        specifiers = []
        String = list(string)
        for i in range(len(String)):
            if String[i] == '%' and String[i+1] == 'd':
                specifiers.append('int')
            if String[i] == '%' and String[i+1] == 'f':
                specifiers.append('float')
            if String[i] == '%' and String[i+1] == 's':
                specifiers.append('str')
        return specifiers
    
    def print_table(self, ast: Node):
        env = SymbolTable()
        self.visit(ast, env)
        print(env.get_symbol_table())