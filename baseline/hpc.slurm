#!/bin/bash
#SBATCH --job-name=citemd_no_rag
#SBATCH --account=torch_pr_1269_tandon_advanced
#SBATCH --gres=gpu:1
#SBATCH --constraint=h200
#SBATCH --comment=preemption=yes;requeue=true
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=00:45:00
#SBATCH --output=baseline/runs/slurm-%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
CITEMD_RUN="baseline/runs/${SLURM_JOB_ID}"
mkdir -p "$CITEMD_RUN"
if [[ -z "${CITEMD_PYTHON:-}" ]]; then
    CITEMD_ENV="${TMPDIR:-/tmp}/citemd-python-${SLURM_JOB_ID}"
    mkdir -p "$CITEMD_ENV"
    tar -xf baseline/local/python313-env.tar -C "$CITEMD_ENV"
    CITEMD_PYTHON="$CITEMD_ENV/env/bin/python"
fi
export PATH="$(dirname "$CITEMD_PYTHON"):$PATH"
export LD_PRELOAD="/usr/lib64/libstdc++.so.6${LD_PRELOAD:+:$LD_PRELOAD}"
export VLLM_USE_FLASHINFER_SAMPLER=0
export HF_HOME=/scratch/atk331/huggingface-cache
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export VLLM_CACHE_ROOT="${TMPDIR:-/tmp}/citemd-vllm-${SLURM_JOB_ID}"
export TRITON_CACHE_DIR="${TMPDIR:-/tmp}/citemd-triton-${SLURM_JOB_ID}"
export TORCHINDUCTOR_CACHE_DIR="${TMPDIR:-/tmp}/citemd-torch-${SLURM_JOB_ID}"
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
"$CITEMD_PYTHON" -m pip freeze > "$CITEMD_RUN/environment.freeze.txt"
nvidia-smi
"$CITEMD_PYTHON" baseline/run.py --out-dir "$CITEMD_RUN/greedy" --thinking off --resume
"$CITEMD_PYTHON" baseline/evaluate.py --run-dir "$CITEMD_RUN/greedy"
"$CITEMD_PYTHON" baseline/run.py --out-dir "$CITEMD_RUN/thinking_low" --thinking low --resume
"$CITEMD_PYTHON" baseline/evaluate.py --run-dir "$CITEMD_RUN/thinking_low"
"$CITEMD_PYTHON" baseline/publish_results.py --job-dir "$CITEMD_RUN"
