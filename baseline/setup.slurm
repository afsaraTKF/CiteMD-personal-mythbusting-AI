#!/bin/bash
#SBATCH --job-name=citemd_setup
#SBATCH --account=torch_pr_1269_tandon_advanced
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=00:30:00
#SBATCH --output=baseline/runs/setup-%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=2
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
module load anaconda3/2025.06
python baseline/bootstrap_env.py --out baseline/local/python313-env.tar
