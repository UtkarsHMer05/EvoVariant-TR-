"""Patch vortex attn_interface for EvoVariant-TR parity (M052).

Runs inside the Modal image build (see evo2_scorer_app.py) to make the
vendored vortex attention interface compatible with flash-attn 2.6.3 /
torch 2.4 return signatures.
"""

import os
import shutil

path = "/usr/local/lib/python3.12/site-packages/vortex/ops/attn_interface.py"

with open(path) as f:
    text = f.read()

text = text.replace(
    "out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.fwd(",
    "res = flash_attn_gpu.fwd(",
)
text = text.replace(
    "out, softmax_lse, S_dmask, rng_state = flash_attn_gpu.varlen_fwd(",
    "res = flash_attn_gpu.varlen_fwd(",
)
text = text.replace(
    'if torch.__version__ >= "2.4.0":',
    "if False:",
)
text = text.replace(
    "return out, softmax_lse, S_dmask, rng_state",
    "_unpack = (res[0], res[-3], res[-2], res[-1]) if isinstance(res, (tuple, list)) "
    "else (res, None, None, None)\n"
    "    out, softmax_lse, S_dmask, rng_state = tuple(\n"
    "        (x.clone() if hasattr(x, 'clone') else x) for x in _unpack\n"
    "    )\n"
    "    return out, softmax_lse, S_dmask, rng_state",
)

with open(path, "w") as f:
    f.write(text)

pycache = "/usr/local/lib/python3.12/site-packages/vortex/ops/__pycache__"
if os.path.exists(pycache):
    shutil.rmtree(pycache)
