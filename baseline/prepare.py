"""Prepare claim-only inputs and audit the retrieval handoff; standard library only."""
import argparse
import csv
import hashlib
import json
import tarfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("Supported", "Refuted", "Insufficient", "Conflicting")
SCIFACT_URL = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"


def read_jsonl(path):
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aggregate(labels):
    labels = set(labels)
    supports = bool(labels & {"Supports", "SUPPORT", "Supported"})
    refutes = bool(labels & {"Refutes", "CONTRADICT", "Refuted"})
    return "Conflicting" if supports and refutes else "Supported" if supports else "Refuted" if refutes else "Insufficient"


def prepare_healthver(directory, original=None):
    claims = read_jsonl(directory / "test_claims.jsonl")
    corpus = read_jsonl(directory / "corpus.jsonl")
    with open(directory / "test_pairs.csv", newline="", encoding="utf-8") as stream:
        pairs = list(csv.DictReader(stream))
    with open(directory / "test_pairs_sample.csv", newline="", encoding="utf-8") as stream:
        sample_reader = csv.DictReader(stream)
        sample_columns = sample_reader.fieldnames
        sample = list(sample_reader)
    assert len({c["cid"] for c in claims}) == len(claims), "Duplicate claim IDs"
    assert len({c["claim"] for c in claims}) == len(claims), "Duplicate claim texts"
    corpus_map = {p["pid"]: p["text"] for p in corpus}
    claim_map = {c["cid"]: c for c in claims}
    pair_labels = defaultdict(set)
    pair_counts = Counter()
    for p in pairs:
        assert p["claim"] == claim_map[p["cid"]]["claim"]
        assert p["evidence"].strip() == corpus_map[p["pid"]].strip()
        pair_labels[p["cid"], p["pid"]].add(p["label"])
        pair_counts[p["cid"]] += 1
    for c in claims:
        assert c["claim_label"] == aggregate(c["label_set"])
        assert c["gold"] == {pid: sorted(labs) for (cid, pid), labs in pair_labels.items() if cid == c["cid"]}
    summary = {
        "corpus_passages": len(corpus), "test_claims": len(claims), "test_pair_rows": len(pairs),
        "unique_claim_passage_pairs": len(pair_labels),
        "duplicate_pair_rows": len(pairs) - len(pair_labels),
        "multi_label_pairs": [{"cid": cid, "pid": pid, "labels": sorted(labs)}
                              for (cid, pid), labs in pair_labels.items() if len(labs) > 1],
        "claim_label_counts": dict(Counter(c["claim_label"] for c in claims)),
        "pair_label_counts": dict(Counter(p["label"] for p in pairs)),
        "unanimous_claims": sum(c["unanimous"] for c in claims),
        "decisive_unconflicted_claims": sum(c["claim_label"] in ("Supported", "Refuted") for c in claims),
        "sample_rows": len(sample), "sample_columns": sample_columns,
        "sample_is_labeled": "label" in sample_columns,
        "source_sha256": {name: sha256(directory / name) for name in
                          ("test_claims.jsonl", "test_pairs.csv", "test_pairs_sample.csv", "corpus.jsonl")},
    }
    if original:
        splits = {}
        for split in ("train", "dev", "test"):
            path = original / f"healthver_{split}.csv"
            with open(path, newline="", encoding="utf-8-sig") as stream:
                splits[split] = list(csv.DictReader(stream))
        test_claims = {p["claim"].strip() for p in splits["test"]}
        assert test_claims == {c["claim"] for c in claims}
        expected_pairs = Counter((p["claim"].strip(), p["evidence"].strip(), p["label"]) for p in splits["test"])
        actual_pairs = Counter((p["claim"].strip(), p["evidence"].strip(), p["label"]) for p in pairs)
        assert actual_pairs == expected_pairs, "Handoff differs from original test pairs"
        overlap = test_claims & {p["claim"].strip() for p in splits["train"]}
        summary["train_test_claim_overlap"] = sorted(overlap)
        summary["original_test_pairs_verified"] = True
    else:
        overlap = set()
    prepared = [{
        "uid": "healthver:" + c["cid"], "cid": c["cid"], "dataset": "healthver", "split": "test",
        "claim": c["claim"], "reference_label": c["claim_label"], "unanimous": c["unanimous"],
        "cluster": str(c["topic"]), "pair_rows": pair_counts[c["cid"]],
        "train_overlap": c["claim"] in overlap,
    } for c in claims]
    return prepared, summary


def download_scifact(directory):
    directory.mkdir(parents=True, exist_ok=True)
    archive_path = directory / "data.tar.gz"
    if not archive_path.exists():
        urllib.request.urlretrieve(SCIFACT_URL, archive_path)
    # Copy only named claim files. Never extract arbitrary archive paths.
    with tarfile.open(archive_path) as archive:
        for split in ("train", "dev", "test"):
            name = f"claims_{split}.jsonl"
            members = [m for m in archive.getmembers() if Path(m.name).name == name and m.isfile()]
            if len(members) != 1:
                raise ValueError(f"Expected exactly one {name} in archive")
            with archive.extractfile(members[0]) as source:
                (directory / name).write_bytes(source.read())
    return {"url": SCIFACT_URL, "archive_sha256": sha256(archive_path)}


def prepare_scifact(directory):
    path = directory / "claims_dev.jsonl"
    claims = read_jsonl(path)
    # Link related claims sharing cited documents so bootstrap intervals do not
    # treat negations/variants from one source as independent observations.
    parent = {str(c["id"]): str(c["id"]) for c in claims}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    first_claim_for_document = {}
    for c in claims:
        for doc in c.get("cited_doc_ids", []):
            cid = str(c["id"])
            if doc in first_claim_for_document:
                parent[find(cid)] = find(first_claim_for_document[doc])
            else:
                first_claim_for_document[doc] = cid
    prepared = []
    for c in claims:
        assert "evidence" in c, "SciFact test is unlabeled: use dev"
        labels = {r["label"] for rationales in c["evidence"].values() for r in rationales}
        prepared.append({
            "uid": f"scifact:{c['id']}", "cid": str(c["id"]), "dataset": "scifact", "split": "dev",
            "claim": c["claim"], "reference_label": aggregate(labels), "unanimous": len(labels) <= 1,
            "cluster": find(str(c["id"])), "pair_rows": 1, "train_overlap": False,
        })
    return prepared, {"split": "dev", "claims": len(prepared), "citation_components": len({r["cluster"] for r in prepared}), "source_sha256": sha256(path),
                      "claim_label_counts": dict(Counter(c["reference_label"] for c in prepared))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-dir", type=Path, default=ROOT / "retrieval/outputs")
    parser.add_argument("--healthver-original", type=Path)
    parser.add_argument("--scifact-dir", type=Path, default=ROOT / "baseline/data/scifact")
    parser.add_argument("--download-scifact", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "baseline/data/evaluation.jsonl")
    parser.add_argument("--audit", type=Path, default=ROOT / "baseline/results/data_audit.json")
    args = parser.parse_args()
    rows, audit = prepare_healthver(args.retrieval_dir, args.healthver_original)
    audit = {"healthver": audit}
    if args.download_scifact:
        audit["scifact_download"] = download_scifact(args.scifact_dir)
    elif (args.scifact_dir / "data.tar.gz").exists():
        audit["scifact_download"] = {"url": SCIFACT_URL, "archive_sha256": sha256(args.scifact_dir / "data.tar.gz")}
    if (args.scifact_dir / "claims_dev.jsonl").exists():
        sci_rows, audit["scifact"] = prepare_scifact(args.scifact_dir)
        rows.extend(sci_rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    audit["evaluation_sha256"] = sha256(args.out)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
