import modal
app = modal.App("download-file")

evo2_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.12"
    )
    .apt_install(
        ["build-essential", "cmake", "ninja-build",
            "libcudnn8", "libcudnn8-dev", "git", "gcc", "g++"]
    )
    .env({
        "CC": "/usr/bin/gcc",
        "CXX": "/usr/bin/g++",
    })
    .run_commands("pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124 && git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git && cd evo2 && pip install .")
    .run_commands("pip uninstall -y transformer-engine transformer_engine")
    .run_commands("pip install 'transformer_engine[pytorch]==1.13' --no-build-isolation")
    .run_commands("pip install --force-reinstall --no-deps https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/flash_attn-2.6.3%2Bcu123torch2.4cxx11abiFALSE-cp312-cp312-linux_x86_64.whl")
)

@app.function(image=evo2_image)
def get_file():
    target = '/usr/local/lib/python3.12/site-packages/vortex/ops/attn_interface.py'
    try:
        with open(target, 'r') as f:
            return f.read()
    except Exception as e:
        return str(e)

@app.local_entrypoint()
def main():
    content = get_file.remote()
    with open('local_attn_interface.py', 'w') as f:
        f.write(content)
