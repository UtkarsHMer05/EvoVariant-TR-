import re
path='local_attn_interface.py'
f=open(path, 'r')
text=f.read()
f.close()
text=text.replace('out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.fwd(', 'res = flash_attn_gpu.fwd(')
text=text.replace('out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.varlen_fwd(', 'res = flash_attn_gpu.varlen_fwd(')

code = """
    _unpack = (res[0], res[-3], res[-2], res[-1]) if type(res) is tuple else (res, None, None, None)
    out, softmax_lse, S_dmask, rng_state = tuple((x.clone() if hasattr(x, 'clone') else x) for x in _unpack)
    return out, softmax_lse, S_dmask, rng_state
"""
text=text.replace('return out, softmax_lse, S_dmask, rng_state', code.strip())
f=open('patched_attn_interface2.py', 'w')
f.write(text)
