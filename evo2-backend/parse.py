import re
path='local_attn_interface.py'
with open(path, 'r') as f: text = f.read()
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'return out, softmax_lse, S_dmask, rng_state' in line:
        print(f"Line {i}: found!")
        start = max(0, i-20)
        end = min(len(lines), i+5)
        for j in range(start, end):
            print(lines[j])
        print("="*40)
