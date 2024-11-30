'''
Tree-walking interpreter
'''
from collections import ChainMap
from rich        import print

from MiniCppAST       import *
from MiniCppChecker   import Checker
from MiniCppBuiltins  import builtins, consts, CallError
from MiniCpptypes     import CObject, Number, String, Bool, Nil, Array


# Veracidad en MiniC
def _is_truthy(value):
  if isinstance(value, bool):
    return value
  elif value is None:
    return False
  else:
    return True

class ReturnException(Exception):
  def __init__(self, value):
    self.value = value

class BreakException(Exception):
  pass

class ContinueException(Exception):
  pass

class MiniCExit(BaseException):
  pass

class AttributeError(Exception):
  pass


class Function:

  def __init__(self, node, env):
    self.node = node
    self.env = env

  @property
  def arity(self) -> int:
    if self.node.params is None:
      self.node.params = []
    return len(self.node.params)

  def __call__(self, interp, *args):
    newenv = self.env
    for name, arg in zip(self.node.params, args):
      if isinstance(name, VarDeclStmt):
        newenv[name.ident] = arg

    oldenv = interp.env
    interp.env = newenv
    try:
      self.node.stmts.accept(interp)
      result = None
    except ReturnException as e:
      result = e.value
    finally:
      interp.env = oldenv
    return result

  def bind(self, instance):
    env = self.env.new_child()
    env['this'] = instance
    return Function(self.node, env)
  
  def is_main(self) -> bool:
    return self.node.ident == "main" and self.arity == 0


class Class:

  def __init__(self, name, sclass, methods):
    self.name = name
    self.sclass  = sclass
    self.methods = methods

  def __str__(self):
    return self.name

  def __call__(self, *args):
    this = Instance(self)
    init = self.find_method('init')
    if init:
      init.bind(this)(*args)
    return this

  def find_method(self, name):
    meth = self.methods.get(name)
    if meth is None and self.sclass:
      return self.sclass.find_method(name)
    return meth


class Instance:

  def __init__(self, klass):
    self.klass = klass
    self.data = { }

  def __str__(self):
    return self.klass.name + " instance"

  def get(self, name):
    if name in self.data:
      return self.data[name]
    method = self.klass.find_method(name)
    if not method:
      raise AttributeError(f'Propiedad indefinida {name}')
    return method.bind(self)

  def set(self, name, value):
    self.data[name] = value


class Interpreter(Visitor):

  def __init__(self, ctxt):
    self.ctxt      = ctxt
    self.env       = ChainMap()
    self.check_env = ChainMap()
    self.localmap  = { }

  def _check_numeric_operands(self, node, left, right):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)) or left is None or right is None:
      return True
    else:
      self.error(node, f"En '{node.opr}' los operandos deben ser numeros")

  def _check_numeric_operand(self, node, value):
    if isinstance(value, (int, float)):
      return True
    else:
      self.error(node, f"En '{node.opr}' el operando debe ser un numero")

  def error(self, position, message):
    self.ctxt.error(position, message)
    raise MiniCExit()

  # Punto de entrada alto-nivel
  def interpret(self, node):

    for name, cval in consts.items():
      self.check_env[name] = cval
      self.env[name] = cval

    for name, func in builtins.items():
      self.check_env[name] = func
      self.env[name] = func

    try:
      Checker.check(node, self.check_env)
      if not self.ctxt.have_errors:
        node.accept(self)
    except ReturnException as e:
      print("\nReturn: ", e.value)
    except MiniCExit as e:
      pass
    
    main = self.env.get('main')
    if main and isinstance(main, Function) and main.is_main():
      main(self)
    else:
      raise MiniCExit()

  # Declarations
  def visit(self, node: Program):
    for decl in node.decls:
      decl.accept(self)
      
      
  def visit(self, node: ClassDeclStmt):
    if node.sclass:
      node.sclass = self.env[node.sclass]
      sclass = node.sclass.accept(self)
      env = self.env.new_child()
      env['super'] = sclass
    else:
      sclass = None
      env = self.env
    methods = { }
    for meth in node.class_body:
      methods[meth.ident] = Function(meth, env)
    cls = Class(node.ident, sclass, methods)
    self.env[node.ident] = cls

  def visit(self, node: FuncDeclStmt):
    func = Function(node, self.env)
    self.env[node.ident] = func

  def visit(self, node: VarDeclStmt):
    if node.expr:
        expr = node.expr.accept(self)
    else:
        expr = None
      
    if id(node) not in self.localmap:
      self.localmap[id(node)] = len(self.env.maps) - 1
    self.env[node.ident] = expr


  # Statements

  def visit(self, node: CompoundStmt):
    if self.env.get('incycle') is False or None or self.env.get('ifstmt') is False or None:
        self.env = self.env.new_child()
    
    for decl in node.decls:
      decl.accept(self)
    
    for stmt in node.stmts:
      stmt.accept(self)
    
    if self.env.get('incycle') is False or None or self.env.get('ifstmt') is False or None:
        self.env = self.env.parents

  def visit(self, node: PrintfStmt):
    error = False
    expr = node.string
    for arg in node.args:
      arg = arg.accept(self)
      if arg is None:
        error = True
      if isinstance(arg, int):
        expr = expr.replace('%d', str(arg), 1)
      elif isinstance(arg, str):
        expr = expr.replace('%s', arg, 1)
      elif isinstance(arg, float):
        expr = expr.replace('%f', str(arg), 1)
      else:
        error = True
      
    if isinstance(expr, str):
      expr = expr.replace('\\n', '\n')
      expr = expr.replace('\\t', '\t')
    if not error:
      print(expr, end='')

  def visit(self, node: WhileStmt):
    self.env['incycle'] = True
    while _is_truthy(node.expr.accept(self)):
      try:
        node.stmt.accept(self)
      except BreakException:
        return
      except ContinueException:
        continue
    self.env['incycle'] = False

  def visit(self, node: IfStmt):
    self.env['ifstmt'] = True
    expr = node.expr.accept(self)
    if _is_truthy(expr):
      node.then.accept(self)
    elif node.else_:
      node.else_.accept(self)
    self.env['ifstmt'] = False

  def visit(self, node: BreakStmt):
    raise BreakException()

  def visit(self, node: ContinueStmt):
    raise ContinueException()

  def visit(self, node: ReturnStmt):
    # Ojo: node.expr es opcional
    value = 0 if not node.expr else node.expr.accept(self)
    raise ReturnException(value)

  def visit(self, node: ExprStmt):
    node.expr.accept(self)
    
  def visit(self, node: NullStmt):
    pass
  
  def visit(self, node: ForStmt):
    self.env['incycle'] = True
    node.init.accept(self)
    while _is_truthy(node.cond.accept(self)):
      try:
        node.stmt.accept(self)
      except BreakException:
        return
      except ContinueException:
        node.iter.accept(self)
        continue
      node.iter.accept(self)
    self.env['incycle'] = False
    
  # Expressions
  def visit(self, node: ConstExpr):
    return node.value

  def visit(self, node: BinaryOpExpr):
    left  = node.left.accept(self)
    right = node.right.accept(self)
    if left is None or right is None:
      return None

    if node.opr == '+':
      (isinstance(left, str) and isinstance(right, str)) or self._check_numeric_operands(node, left, right)
      return left + right

    elif node.opr == '-':
      self._check_numeric_operands(node, left, right)
      return left - right

    elif node.opr == '*':
      self._check_numeric_operands(node, left, right)
      return left * right

    elif node.opr == '/':
      self._check_numeric_operands(node, left, right)
      if isinstance(left, int) and isinstance(right, int):
        return left // right

      return left / right

    elif node.opr == '%':
      self._check_numeric_operands(node, left, right)
      return left % right

    elif node.opr == '==':
      return left == right

    elif node.opr == '!=':
      return left != right

    elif node.opr == '<':
      self._check_numeric_operands(node, left, right)
      return left < right

    elif node.opr == '>':
      self._check_numeric_operands(node, left, right)
      return left > right

    elif node.opr == '<=':
      self._check_numeric_operands(node, left, right)
      return left <= right

    elif node.opr == '>=':
      self._check_numeric_operands(node, left, right)
      return left >= right

    else:
      raise NotImplementedError(f"Mal operador {node.op}")
    
  def visit(self, node: LogicalOpExpr):
    left = node.left.accept(self)
    if node.op == '||':
      return left if _is_truthy(left) else node.right.accept(self)
    if node.op == '&&':
      return node.right.accept(self) if _is_truthy(left) else left
    raise NotImplementedError(f"Mal operador {node.op}")

  def visit(self, node: UnaryOpExpr):
    expr = node.expr.accept(self)
    if node.opr == "-":
      self._check_numeric_operand(node, expr)
      return - expr
    elif node.opr == "!":
      return not _is_truthy(expr)
    else:
      raise NotImplementedError(f"Mal operador {node.op}")

  def visit(self, node: Grouping):
    return node.expr.accept(self)

  def visit(self, node: VarAssignmentExpr):
    expr = node.expr.accept(self)
    if id(node) not in self.localmap:
      self.localmap[id(node)] = len(self.env.maps) - 1
    self.env.maps[self.localmap[id(node)]][node.var] = expr
    return expr
    
    
  def visit(self, node: OperatorAssign):
    expr = node.expr1.accept(self)
    if node.op == '+=':
      self.env.maps[self.localmap[id(node)]][node.expr] += expr
    elif node.op == '-=':
      self.env.maps[self.localmap[id(node)]][node.expr] -= expr
    elif node.op == '*=':
      self.env.maps[self.localmap[id(node)]][node.expr] *= expr
    elif node.op == '/=':
      self.env.maps[self.localmap[id(node)]][node.expr] /= expr
    elif node.op == '%=':
      self.env.maps[self.localmap[id(node)]][node.expr] %= expr

  def visit(self, node: PreInc):
    if id(node) not in self.localmap:
        self.localmap[id(node)] = len(self.env.maps) - 1
    self.env.maps[self.localmap[id(node)]][node.ident] += 1
    return self.env.maps[self.localmap[id(node)]][node.expr]

  def visit(self, node: PreDec):
    if id(node) not in self.localmap:
        self.localmap[id(node)] = len(self.env.maps) - 1
    self.env.maps[self.localmap[id(node)]][node.expr] -= 1
    return self.env.maps[self.localmap[id(node)]][node.expr]

  def visit(self, node: PostInc):
    if id(node) not in self.localmap:
     self.localmap[id(node)] = len(self.env.maps) -1 
    self.env.maps[self.localmap[id(node)]][node.expr.ident] += 1
    print(self.env)
    print(self.localmap)
    return self.env.maps[self.localmap[id(node)]][node.expr.ident]

  def visit(self, node: PostDec):
    if id(node) not in self.localmap:
        self.localmap[id(node)] = len(self.env.maps) - 1
    self.env.maps[self.localmap[id(node)]][node.expr] -= 1
    return self.env.maps[self.localmap[id(node)]][node.expr]

  def visit(self, node: CallExpr):
    callee = self.env[node.ident]
    if not callable(callee):
      self.error(node.ident, f'{self.ctxt.find_source(node.ident)!r} no es invocable')

    args = [ arg.accept(self) for arg in node.args ]

    if callee.arity != -1 and len(args) != callee.arity:
      self.error(node.ident, f"Experado {callee.arity} argumentos")
      
    try:
      return callee(self, *args)
    except CallError as err:
      self.error(node.ident, str(err))

  def visit(self, node: VarExpr):
    if id(node) not in self.localmap:
      self.localmap[id(node)] = len(self.env.maps) - 1
    return self.env.maps[self.localmap[id(node)]][node.ident]

  def visit(self, node: Set):
    obj = node.obj.accept(self)
    val = node.value.accept(self)
    if isinstance(obj, Instance):
      obj.set(node.name, val)
      return val
    else:
      self.error(node.obj, f'{self.ctxt.find_source(node.obj)!r} no es una instancia')

  def visit(self, node: Get):
    obj = node.obj.accept(self)
    if isinstance(obj, Instance):
      try:
        return obj.get(node.name)
      except AttributeError as err:
        self.error(node.obj, str(err))
    else:
      self.error(node.obj, f'{self.ctxt.find_source(node.obj)!r} no es una instancia')

  def visit(self, node: This):
    return self.env.maps[self.localmap[id(node)]]['this']

  def visit(self, node: Super):
    distance = self.localmap[id(node)]
    sclass = self.env.maps[distance]['super']
    this = self.env.maps[distance-1]['this']
    method = sclass.find_method(node.name)
    if not method:
      self.error(node.object, f'Propiedad indefinida {node.name!r}')
    return method.bind(this)
  
#======================================================================================
  
  def visit(self, node: ArrayDeclStmt):
    self.env[node.ident] = {
      'type': node._type,
      'ident': node.ident,
      'value': []
    }
  
  def visit(self, node: ArrayAssignmentExpr):
    array = self.env[node.ident]
    index = node.expr0.accept(self)
    value = node.expr1.accept(self)
    array['value'][index] = value
    return value