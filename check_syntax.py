with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[448:456], start=449):
        print(f'{i}: {repr(line)}')
