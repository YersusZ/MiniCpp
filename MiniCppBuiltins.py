class CallError(Exception):
    def __init__(self, message):
        super().__init__(message)

def printf_builtin(value):
    print(value)

def scanf_builtin(prompt):
    return input(prompt)

def len_builtin(value):
    return len(value)

def type_builtin(value):
    return type(value).__name__


builtins = {
    'print': printf_builtin,
    'input': scanf_builtin,
    'len': len_builtin,
    'type': type_builtin,
}


consts = {
    'PI': 3.14159,
    'E': 2.71828,
    'TRUE': True,
    'FALSE': False,
    'NULL': None,
}