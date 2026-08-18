import re
path='local_attn_interface.py'
f=open(path, 'r')
text=f.read()
f.close()
text=text.replace('out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.fwd(', 'res = flash_attn_gpu.fwd(')
text=text.replace('out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.varlen_fwd(', 'res = flash_attn_gpu.varlen_fwd(')
text=text.replace('return out, softmax_lse, S_dmask, rng_state', 'out, softmax_lse, S_dmask, rng_state = (res[0], res[-3], res[-2], res[-1]) if type(res) is tuple else (res, None, None, None)\n    return out, softmax_lse, S_dmask, rng_state')
f=open('patched_attn_interface.py', 'w')
f.write(text)
