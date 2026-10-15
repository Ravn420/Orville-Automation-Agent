import py_compile
try:
    py_compile.compile('orville_core/endpoint_monitor.py', doraise=True)
    print('File compiles successfully')
except SyntaxError as e:
    print(f'Syntax error: {e}')
