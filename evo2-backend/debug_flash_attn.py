import modal
app = modal.App("debug-flash-attn")

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
    .run_commands("pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/flash_attn-2.6.3%2Bcu123torch2.4cxx11abiFALSE-cp312-cp312-linux_x86_64.whl")
)

@app.function(image=evo2_image, gpu="H100")
def test_flash_attn():
    import torch
    import flash_attn_2_cuda as flash_attn_gpu
    q = torch.randn(1, 10, 2, 8, dtype=torch.bfloat16, device="cuda")
    cu_seqlens = torch.tensor([0, 10], dtype=torch.int32, device="cuda")
    print(flash_attn_gpu.fwd(
        q, q, q, cu_seqlens, cu_seqlens, 10, 10, 0.0, 1.0, False, False, 1, False, None
    ))

@app.local_entrypoint()
def main():
    test_flash_attn.remote()
