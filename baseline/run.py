"""Run a frozen, claim-only Qwen baseline on an allocated GPU. No retrieval calls."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from pathlib import Path

from prepare import LABELS, ROOT, read_jsonl, sha256

SYSTEM = """You assess medical and scientific claims carefully using your existing knowledge.
No external sources, search, retrieved passages, or tools are available.
Evaluate the exact claim, including its population, intervention, dose, time, and strength.
Use these labels:
Supported: your knowledge supports the claim as written.
Refuted: your knowledge contradicts the claim as written.
Insufficient: you lack enough reliable knowledge to decide, or the claim is too underspecified.
Conflicting: you know substantive support and substantive contradiction for the exact claim
and cannot resolve that conflict. Controversy or somebody reporting a belief alone is not support.
Do not invent studies, citations, URLs, or evidence. Do not infer what a hidden passage says.
Return one JSON object with label, confidence (a number from 0 to 1 representing your
confidence that your selected label is correct), and reason (at most two concise sentences)."""

def messages_for(row):
    # Deliberately whitelist claim text. Gold, topic, question, passage IDs,
    # dataset name, and references must never enter the model's input.
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Assess this claim:\n" + row["claim"]}]


def parse_answer(text, finish_reason):
    if finish_reason != "stop":
        return None, "generation_" + str(finish_reason)
    final = text.rsplit("</think>", 1)[-1].strip()
    if final.startswith("```json") and final.endswith("```"):
        final = final[7:-3].strip()
    try:
        result = json.loads(final)
    except (json.JSONDecodeError, TypeError):
        return None, "invalid_json"
    if not isinstance(result, dict) or result.get("label") not in LABELS:
        return None, "invalid_label"
    confidence = result.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return None, "invalid_confidence"
    if not isinstance(result.get("reason"), str):
        return None, "invalid_reason"
    return result, None


def command_output(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "baseline/data/evaluation.jsonl")
    parser.add_argument("--model-manifest", type=Path, default=ROOT / "baseline/results/model_manifest.json")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--thinking", choices=("off", "low"), default="off")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--max-model-len", type=int, default=8192)
    parser.add_argument("--resume", action="store_true", help="Resume only an identical, validated experiment")
    args = parser.parse_args()
    os.environ["VLLM_USE_FLASHINFER_SAMPLER"] = "0"
    import torch
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    if not torch.cuda.is_available():
        raise RuntimeError("Use a Slurm GPU allocation; do not run inference on a login node")
    rows = read_jsonl(args.input)
    if args.limit:
        rows = rows[:args.limit]
    if len({r["uid"] for r in rows}) != len(rows):
        raise ValueError("Duplicate evaluation IDs")
    model_manifest = json.loads(args.model_manifest.read_text())
    model_path = model_manifest["local_path"]
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    template_kwargs = {"enable_thinking": args.thinking != "off"}
    if args.thinking != "off":
        template_kwargs["reasoning_effort"] = args.thinking
    prompts = [tokenizer.apply_chat_template(messages_for(row), tokenize=False,
                                              add_generation_prompt=True, **template_kwargs) for row in rows]
    max_tokens = 512 if args.thinking == "off" else 4096
    prompt_lengths = [len(tokenizer.encode(p, add_special_tokens=False)) for p in prompts]
    if max(prompt_lengths) + max_tokens > args.max_model_len:
        raise ValueError("Input + output exceeds context; do not silently truncate claims")
    sampling_kwargs = {"temperature": 0.0 if args.thinking == "off" else 1.0,
                       "top_p": 1.0 if args.thinking == "off" else 0.95,
                       "top_k": -1 if args.thinking == "off" else 20,
                       "max_tokens": max_tokens, "seed": args.seed,
                       "repetition_penalty": 1.0, "presence_penalty": 0.0}
    # Free generation preserves format failures and does not force a correct class.
    # Thinking runs must be allowed to produce their reasoning before the JSON.
    sampling = SamplingParams(**sampling_kwargs)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "protocol": "closed_book_v1", "model": model_manifest["model"],
        "revision": model_manifest["revision"], "thinking": args.thinking,
        "sampling": sampling_kwargs, "chat_template_kwargs": template_kwargs,
        "system_prompt": SYSTEM, "system_prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "input_sha256": sha256(args.input), "run_script_sha256": sha256(Path(__file__)),
        "prompt_bundle_sha256": hashlib.sha256(json.dumps(prompts, ensure_ascii=False).encode()).hexdigest(),
        "n": len(rows), "max_input_tokens": max(prompt_lengths), "batch_size": args.batch_size,
        "tensor_parallel_size": args.tensor_parallel_size, "max_model_len": args.max_model_len,
        "dtype": "bfloat16", "quantization": None, "enforce_eager": True,
        "gpu_memory_utilization": 0.85, "max_num_seqs": args.batch_size,
        "language_model_only": True, "external_evidence_provided": False,
        "gdn_prefill_backend": "triton",
        "sampler_backend": "pytorch", "libstdcpp_preload": "/usr/lib64/libstdc++.so.6",
        "python": platform.python_version(), "hostname": platform.node(),
        "versions": {name: importlib.metadata.version(name) for name in ("vllm", "torch", "transformers", "tokenizers")},
        "git_commit": command_output(["git", "rev-parse", "HEAD"]),
        "git_status": command_output(["git", "status", "--porcelain"]),
        "gpu": command_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    manifest_path = args.out_dir / "manifest.json"
    predictions_path = args.out_dir / "predictions.jsonl"
    completed = 0
    if predictions_path.exists():
        if not args.resume:
            raise FileExistsError(f"Refusing to overwrite {predictions_path}; choose a new run directory")
        previous = json.loads(manifest_path.read_text())
        for key in ("revision", "input_sha256", "run_script_sha256", "prompt_bundle_sha256", "thinking", "sampling", "batch_size", "dtype", "quantization"):
            if previous[key] != metadata[key]:
                raise ValueError(f"Cannot resume changed experiment: {key}")
        existing = read_jsonl(predictions_path)
        completed = len(existing)
        if [r["uid"] for r in existing] != [r["uid"] for r in rows[:completed]]:
            raise ValueError("Existing predictions do not match the expected claim prefix")
        if previous.get("complete"):
            if completed != len(rows) or sha256(predictions_path) != previous["predictions_sha256"]:
                raise ValueError("Completed experiment was modified")
            print(f"Verified complete run: {args.out_dir}; skipping inference", flush=True)
            return
        metadata["resume_history"] = previous.get("resume_history", []) + [{"previous_completed": completed, "hostname": platform.node()}]
    manifest_path.write_text(json.dumps(metadata, indent=2) + "\n")
    # Preserve exact text presented to the tokenizer for independent leakage audits.
    with (args.out_dir / "prompts.jsonl").open("w", encoding="utf-8") as stream:
        for row, prompt in zip(rows, prompts):
            stream.write(json.dumps({"uid": row["uid"], "prompt": prompt}, ensure_ascii=False) + "\n")
    started = time.monotonic()
    llm = LLM(model=model_path, tokenizer=model_path, dtype="bfloat16", trust_remote_code=False,
              tensor_parallel_size=args.tensor_parallel_size, max_model_len=args.max_model_len,
              gpu_memory_utilization=0.85, max_num_seqs=args.batch_size, seed=args.seed,
              enforce_eager=True, language_model_only=True, enable_prefix_caching=True,
              gdn_prefill_backend="triton")
    metadata["load_seconds"] = time.monotonic() - started
    generation_started = time.monotonic()
    with predictions_path.open("a" if predictions_path.exists() else "x", encoding="utf-8") as stream:
        for offset in range(completed, len(rows), args.batch_size):
            batch_started = time.monotonic()
            outputs = llm.generate(prompts[offset:offset + args.batch_size], sampling, use_tqdm=False)
            elapsed = time.monotonic() - batch_started
            for row, output in zip(rows[offset:offset + args.batch_size], outputs):
                candidate = output.outputs[0]
                parsed, error = parse_answer(candidate.text, candidate.finish_reason)
                record = {"uid": row["uid"], "dataset": row["dataset"], "claim": row["claim"],
                          "prediction": parsed["label"] if parsed else None,
                          "confidence": parsed["confidence"] if parsed else None,
                          "reason": parsed["reason"] if parsed else None,
                          "parse_error": error, "finish_reason": candidate.finish_reason,
                          "input_tokens": len(output.prompt_token_ids),
                          "output_tokens": len(candidate.token_ids), "batch_seconds": elapsed,
                          "raw_output": candidate.text}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            print(f"{args.thinking}: completed {min(offset + args.batch_size, len(rows))}/{len(rows)}", flush=True)
    metadata["generation_seconds"] = time.monotonic() - generation_started
    metadata["total_seconds"] = time.monotonic() - started
    metadata["predictions_sha256"] = sha256(predictions_path)
    metadata["complete"] = True
    manifest_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"out_dir": str(args.out_dir), "seconds": metadata["total_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
