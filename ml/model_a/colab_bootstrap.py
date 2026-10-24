"""Self-contained Colab bootstrap for MedMatch Model A.

`colab exec -f` / `colab run` sends ONE file to the remote kernel; sibling files
are NOT auto-synced. This script therefore bootstraps everything itself:

1. prints GPU inventory (nvidia-smi + torch)
2. installs pinned deps
3. checks out the project at the pinned branch/SHA (authenticated git)
4. verifies the HF token with a cheap metadata call (never prints it)
5. prepare_data -> train --smoke -> baseline+tuned evaluate -> persist to Drive
6. prints a machine-readable RESULT json block and stops.

Secrets: reads HF_TOKEN from Colab Secrets (google.colab.userdata) or env.
Never echoes the token. Keeps caches in /content; copies only the adapter +
metrics + logs to /content/drive/MyDrive/medgemma-model-a.

Tunable via environment variables (set before exec):
    REPO_URL, GIT_REF, PRIMARY_N, SECONDARY_N, TEST_LIMIT, STAGE
"""

import json
import os
import subprocess
import sys
import time

REPO_URL = os.environ.get(
    "REPO_URL", "https://github.com/RayyanSarfraz/Hackachusetts----Rayyan-Muhammad-Camden.git"
)
GIT_REF = os.environ.get("GIT_REF", "feature/model-a-medgemma-finetune")
PRIMARY_N = int(os.environ.get("PRIMARY_N", "1000"))
SECONDARY_N = int(os.environ.get("SECONDARY_N", "150"))
TEST_LIMIT = int(os.environ.get("TEST_LIMIT", "40"))
STAGE = os.environ.get("STAGE", "full")  # smoke | full
WORK = "/content/medmatch"
PROJ = f"{WORK}/ml/model_a"
DRIVE = "/content/drive/MyDrive/medgemma-model-a"


def sh(cmd, **kw):
    print(f"$ {cmd}", flush=True)
    return subprocess.run(cmd, shell=True, check=True, **kw)


def gpu_inventory():
    print("=== nvidia-smi ===", flush=True)
    subprocess.run("nvidia-smi || echo 'no nvidia-smi'", shell=True)
    try:
        import torch

        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            print(json.dumps({
                "name": p.name,
                "vram_gb": round(p.total_memory / 1024**3, 2),
                "cuda": torch.version.cuda,
                "cc": f"{p.major}.{p.minor}",
                "bf16": torch.cuda.is_bf16_supported(),
            }, indent=2), flush=True)
    except Exception as e:
        print(f"torch not ready yet: {e!r}", flush=True)


def get_hf_token():
    tok = os.environ.get("HF_TOKEN")
    if not tok:
        try:
            from google.colab import userdata  # type: ignore

            tok = userdata.get("HF_TOKEN")
        except Exception:
            tok = None
    return tok


def verify_hf_token(tok, model_id):
    """Cheap metadata call before multi-GB download. Never prints the token."""
    from huggingface_hub import HfApi

    api = HfApi(token=tok)
    info = api.model_info(model_id)  # raises if no access
    print(f"[hf] access OK to {model_id} (sha {info.sha[:8]})", flush=True)


def main():
    t_start = time.time()
    result = {"stage": STAGE, "steps": {}}

    gpu_inventory()

    print("=== install deps ===", flush=True)
    sh("pip -q install -U 'transformers>=4.44' 'peft>=0.12' 'trl>=0.9' "
       "'bitsandbytes>=0.43' 'accelerate>=0.33' 'datasets>=2.20' huggingface_hub pyyaml")

    print("=== checkout project ===", flush=True)
    sh(f"rm -rf {WORK} && git clone --depth 1 -b {GIT_REF} {REPO_URL} {WORK}")
    sha = subprocess.check_output(f"cd {WORK} && git rev-parse --short HEAD", shell=True).decode().strip()
    result["git_sha"] = sha
    result["git_ref"] = GIT_REF

    tok = get_hf_token()
    if not tok:
        result["blocker"] = "HF_TOKEN not found in Colab Secrets or env"
        print("RESULT " + json.dumps(result), flush=True)
        sys.exit(3)
    model_id = "google/medgemma-1.5-4b-it"
    verify_hf_token(tok, model_id)
    os.environ["HF_TOKEN"] = tok
    os.environ["HUGGING_FACE_HUB_TOKEN"] = tok

    # mount drive for persistence
    try:
        from google.colab import drive  # type: ignore

        drive.mount("/content/drive")
    except Exception as e:
        print(f"[drive] mount skipped: {e!r}", flush=True)

    sys.path.insert(0, PROJ)
    os.chdir(PROJ)

    print("=== prepare data ===", flush=True)
    sh(f"python prepare_data.py --out /content/data "
       f"--primary-n {PRIMARY_N} --secondary-n {SECONDARY_N}")
    result["steps"]["prepare"] = "ok"

    print("=== train: smoke (forward/backward) ===", flush=True)
    sh("python train.py --data /content/data --out /content/outputs --smoke")
    result["steps"]["smoke"] = "ok"

    if STAGE == "smoke":
        result["runtime_sec"] = round(time.time() - t_start, 1)
        print("RESULT " + json.dumps(result), flush=True)
        return

    print("=== train: full LoRA ===", flush=True)
    sh(f"python train.py --data /content/data --out /content/outputs --drive {DRIVE}")
    result["steps"]["train"] = "ok"

    print("=== evaluate: baseline vs tuned ===", flush=True)
    sh(f"python evaluate.py --data /content/data --adapter /content/outputs/adapter "
       f"--out /content/outputs/metrics --limit {TEST_LIMIT}")
    result["steps"]["evaluate"] = "ok"

    # copy metrics to Drive too
    sh(f"mkdir -p {DRIVE} && cp -r /content/outputs/metrics {DRIVE}/ || true")

    # surface the key artifacts into the RESULT block
    try:
        with open("/content/outputs/run_log.json") as f:
            result["run_log"] = json.load(f)
    except Exception:
        pass
    try:
        with open("/content/outputs/metrics/metrics.json") as f:
            result["metrics"] = json.load(f)
    except Exception:
        pass

    result["runtime_sec"] = round(time.time() - t_start, 1)
    result["artifacts_drive"] = DRIVE
    print("RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
