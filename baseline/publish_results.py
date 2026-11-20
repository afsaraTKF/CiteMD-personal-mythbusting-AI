"""Copy complete experiment artifacts into the versionable results directory."""
import argparse
import json
import shutil
from pathlib import Path

from prepare import ROOT, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    destination = args.out_dir or ROOT / "baseline/results" / args.job_dir.name
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    artifacts = []
    for mode in ("greedy", "thinking_low"):
        source = args.job_dir / mode
        manifest = json.loads((source / "manifest.json").read_text())
        if not manifest.get("complete") or sha256(source / "predictions.jsonl") != manifest["predictions_sha256"]:
            raise ValueError(f"Incomplete or modified run: {source}")
        for name in ("manifest.json", "predictions.jsonl", "prompts.jsonl", "metrics.json", "summary.md", "review_queue.csv"):
            artifacts.append((source / name, destination / mode / name))
    artifacts.append((args.job_dir / "environment.freeze.txt", destination / "environment.freeze.txt"))
    if not all(source.is_file() for source, _ in artifacts):
        raise ValueError("A required artifact is missing")
    checksums = {}
    for source, target in artifacts:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        checksums[str(target.relative_to(destination))] = sha256(target)
    (destination / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n")
    print(f"Complete results copied to {destination}; no git commit or push performed.")


if __name__ == "__main__":
    main()
