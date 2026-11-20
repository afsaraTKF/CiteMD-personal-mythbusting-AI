"""Build on local disk, then archive a relocatable Python runtime for GPU nodes."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "baseline/local/python-env.tar")
    args = parser.parse_args()
    destination = args.out.resolve()
    if destination.exists():
        raise FileExistsError(f"Choose a new archive path instead of overwriting {destination}")
    stage = Path(tempfile.mkdtemp(prefix="citemd-python-", dir="/tmp"))
    environment = stage / "env"
    print(f"Building isolated environment in {environment}", flush=True)
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    python = environment / "bin/python"
    subprocess.run([str(python), "-m", "pip", "install", "--no-compile", "-r", str(ROOT / "baseline/requirements.txt")], check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    subprocess.run([str(python), str(ROOT / "baseline/preflight.py")], check=True)
    freeze = subprocess.check_output([str(python), "-m", "pip", "freeze"], text=True)
    (ROOT / "baseline/results/environment.freeze.txt").write_text(freeze)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-C", str(stage), "-cf", str(destination), "env"], check=True)
    with destination.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {"archive": str(destination), "sha256": digest, "build_directory": str(environment),
                "python": sys.version, "note": "Invoke bin/python -m modules; console-script shebangs retain build paths."}
    destination.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
