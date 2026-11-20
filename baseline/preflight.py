"""CPU-only compatibility and exact-prompt checks; never loads model weights."""
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sysconfig
import tempfile
from pathlib import Path

from prepare import ROOT, read_jsonl
from run import messages_for


def main():
    from transformers import AutoConfig, AutoTokenizer
    from vllm import SamplingParams
    manifest = json.loads((ROOT / "baseline/results/model_manifest.json").read_text())
    path = manifest["local_path"]
    config = AutoConfig.from_pretrained(path, local_files_only=True, trust_remote_code=False)
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
    rows = read_jsonl(ROOT / "baseline/data/evaluation.jsonl")
    result = {"model_type": config.model_type,
              "versions": {name: importlib.metadata.version(name) for name in ("vllm", "torch", "transformers")},
              "n": len(rows), "modes": {}, "loads_weights": False}
    include = Path(sysconfig.get_path("include"))
    if not (include / "Python.h").is_file():
        raise RuntimeError(f"Triton requires Python development headers: missing {include / 'Python.h'}")
    compiler = shutil.which("gcc") or shutil.which("cc")
    if not compiler:
        raise RuntimeError("Triton requires a C compiler")
    with tempfile.TemporaryDirectory(prefix="citemd-headers-") as directory:
        subprocess.run([compiler, "-shared", "-fPIC", "-I" + str(include), "-x", "c", "-", "-o", str(Path(directory) / "probe.so")],
                       input="#include <Python.h>\nPyMODINIT_FUNC PyInit_citemdprobe(void) { return NULL; }\n", text=True, check=True)
    result["python_headers"] = str(include)
    result["c_extension_compile_check"] = True
    for mode in ("off", "low"):
        kwargs = {"enable_thinking": mode != "off"}
        if mode != "off":
            kwargs["reasoning_effort"] = mode
        prompts = [tokenizer.apply_chat_template(messages_for(r), tokenize=False, add_generation_prompt=True, **kwargs) for r in rows]
        lengths = [len(tokenizer.encode(p, add_special_tokens=False)) for p in prompts]
        result["modes"][mode] = {"max_input_tokens": max(lengths),
                                 "prompt_bundle_sha256": hashlib.sha256(json.dumps(prompts, ensure_ascii=False).encode()).hexdigest()}
        assert max(lengths) + (512 if mode == "off" else 4096) <= 8192
    SamplingParams(temperature=0, top_p=1, top_k=-1, max_tokens=512, seed=42)
    output = ROOT / "baseline/results/cpu_preflight.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
