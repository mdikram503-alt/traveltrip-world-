content = open('public/index.html', encoding='utf-8').read()
import re

for var_name in ['Se', 'Jl', 'zr', 'Ln', 'ue']:
    m = re.search(rf'\[{var_name},\s*(\w+)\]\s*=\s*(\w+)\(([^)]*)\)', content)
    if m:
        print(f"[{var_name}, {m.group(1)}] = {m.group(2)}({m.group(3)})")
