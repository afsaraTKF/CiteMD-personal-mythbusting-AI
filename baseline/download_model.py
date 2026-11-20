"""Pin and download the requested public checkpoint before allocating a GPU."""
import argparse
import hashlib
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen3.8-27B")
    parser.add_argument("--cache-dir", type=Path, default=Path("/scratch/atk331/huggingface-cache/hub"))
    parser.add_argument("--manifest", type=Path, default=Path("baseline/results/model_manifest.json"))
    args = parser.parse_args()
    with urllib.request.urlopen(f"https://huggingface.co/api/models/{args.model}?blobs=true", timeout=60) as response:
        info = json.load(response)
    files = [{"name": f["rfilename"], "size": f.get("size"), "sha256": f.get("lfs", {}).get("sha256")}
             for f in info["siblings"] if f["rfilename"].endswith((".json", ".jinja", ".safetensors", ".model"))]
    revision = info["sha"]
    print(json.dumps({"model": args.model, "revision": revision, "download_bytes": sum(f["size"] or 0 for f in files)}), flush=True)
    path = args.cache_dir / ("models--" + args.model.replace("/", "--")) / "snapshots" / revision
    path.mkdir(parents=True, exist_ok=True)

    def download(file):
        target = path / file["name"]
        if target.is_file() and file["size"] is not None and target.stat().st_size == file["size"]:
            # Revalidate any existing large files before trusting a resumed download.
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest() if file["sha256"] else None
            if digest == file["sha256"]:
                return
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".partial")
        for attempt in range(3):
            try:
                digest = hashlib.sha256()
                size = 0
                url = f"https://huggingface.co/{args.model}/resolve/{revision}/{file['name']}"
                with urllib.request.urlopen(url, timeout=180) as source, temporary.open("wb") as destination:
                    while chunk := source.read(8 * 1024 * 1024):
                        destination.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                if file["size"] is not None and size != file["size"]:
                    raise ValueError(f"Size mismatch: {file['name']}")
                if file["sha256"] and digest.hexdigest() != file["sha256"]:
                    raise ValueError(f"SHA256 mismatch: {file['name']}")
                temporary.replace(target)
                print(f"Verified {file['name']} ({size} bytes)", flush=True)
                return
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(download, files))
    manifest = {"model": args.model, "revision": revision, "local_path": str(path), "files": files}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Downloaded pinned checkpoint to {path}", flush=True)


if __name__ == "__main__":
    main()
