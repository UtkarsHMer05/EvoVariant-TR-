path='local_attn_interface.py'
with open(path, 'r') as f: text = f.read()
text = text.replace('if torch.__version__ >= "2.4.0":', 'if False:')
with open('patched_attn_interface3.py', 'w') as f: f.write(text)
