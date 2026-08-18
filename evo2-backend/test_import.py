import modal
app = modal.App("test-import")

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
    .run_commands("MAX_JOBS=4 CXXFLAGS='-D_GLIBCXX_USE_CXX11_ABI=0' pip install psutil ninja && MAX_JOBS=4 CXXFLAGS='-D_GLIBCXX_USE_CXX11_ABI=0' pip install flash-attn==2.6.3 --no-build-isolation")
)

@app.function(image=evo2_image)
def test_imports():
    import torch
    print("Torch version:", torch.__version__)
    import flash_attn_2_cuda
    print("Flash_attn_2_cuda imported")

@app.local_entrypoint()
def main():
    test_imports.remote()
