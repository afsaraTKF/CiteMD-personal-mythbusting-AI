"""Tests for leakage and evaluation errors that would invalidate the experiment."""
import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluate import main as evaluate_main, metrics
from compare import paired_metrics
from prepare import aggregate, sha256
from run import messages_for, parse_answer


class ScientificIntegrityTests(unittest.TestCase):
    def test_paired_comparison_resamples_whole_clusters(self):
        rows = [{"cluster": "one-topic", "greedy_correct": a, "thinking_correct": b, "label_changed": a != b}
                for a, b in ((1, 0), (0, 1), (0, 1), (1, 1))]
        result = paired_metrics(rows, repeats=20)
        self.assertEqual(result["thinking_minus_greedy"], .25)
        self.assertEqual(result["wrong_to_right"], 2)
        self.assertEqual(result["right_to_wrong"], 1)
        self.assertEqual(result["paired_delta_95pct_cluster_bootstrap"]["lower"], .25)
        self.assertEqual(result["paired_delta_95pct_cluster_bootstrap"]["upper"], .25)

    def test_no_reference_or_passage_leakage(self):
        row = {"claim": "An example claim", "reference_label": "SECRET_REFERENCE",
               "evidence": "SECRET_PASSAGE", "question": "SECRET_QUESTION", "topic": "SECRET_TOPIC"}
        text = json.dumps(messages_for(row))
        self.assertIn(row["claim"], text)
        self.assertNotIn("SECRET_", text)

    def test_invalid_predictions_stay_in_denominator(self):
        rows = [{"reference_label": "Supported", "prediction": "Supported", "confidence": 0.9},
                {"reference_label": "Refuted", "prediction": None, "confidence": None}]
        result = metrics(rows)
        self.assertEqual(result["accuracy"], 0.5)
        self.assertEqual(result["invalid_outputs"], 1)
        self.assertEqual(result["per_class"]["Refuted"]["recall"], 0)

    def test_support_refute_conflict_is_never_majority_vote(self):
        self.assertEqual(aggregate(["Supports"] * 10 + ["Refutes"]), "Conflicting")
        self.assertEqual(aggregate(["Neutral", "Supports"]), "Supported")

    def test_truncated_output_is_not_a_valid_prediction(self):
        answer = '{"label":"Supported","confidence":0.9,"reason":"ok"}'
        self.assertIsNone(parse_answer(answer, "length")[0])

    def test_reasoning_text_cannot_override_final_label(self):
        answer = '<think>Perhaps Supported?</think>{"label":"Refuted","confidence":0.9,"reason":"No"}'
        self.assertEqual(parse_answer(answer, "stop")[0]["label"], "Refuted")
        self.assertIsNone(parse_answer("Supported Refuted Insufficient", "stop")[0])

    def test_confidence_must_be_numeric_probability(self):
        for value in (True, "0.9", 1.2, float("nan")):
            answer = json.dumps({"label": "Supported", "confidence": value, "reason": "ok"})
            self.assertIsNone(parse_answer(answer, "stop")[0])

    def test_complete_file_evaluation_and_changed_input_rejection(self):
        with tempfile.TemporaryDirectory(prefix="citemd-test-") as directory:
            root = Path(directory)
            references = [{"uid": str(i), "dataset": "healthver", "claim": f"claim {i}",
                           "reference_label": label, "unanimous": True, "cluster": str(i),
                           "train_overlap": False} for i, label in enumerate(("Supported", "Refuted"))]
            predictions = [{"uid": str(i), "dataset": "healthver", "claim": f"claim {i}",
                            "prediction": "Supported" if i == 0 else None,
                            "confidence": 0.9 if i == 0 else None, "reason": "fixture"}
                           for i in range(2)]
            source = root / "input.jsonl"
            output = root / "predictions.jsonl"
            source.write_text("".join(json.dumps(r) + "\n" for r in references))
            output.write_text("".join(json.dumps(r) + "\n" for r in predictions))
            (root / "manifest.json").write_text(json.dumps({
                "model": "synthetic-test-fixture", "revision": "fixture", "thinking": "off",
                "input_sha256": sha256(source), "predictions_sha256": sha256(output), "n": 2, "complete": True}))
            with patch("sys.argv", ["evaluate.py", "--input", str(source), "--run-dir", str(root)]), contextlib.redirect_stdout(io.StringIO()):
                evaluate_main()
                report = json.loads((root / "metrics.json").read_text())
                self.assertEqual(report["results"]["healthver"]["all_claims_reference_agreement"]["accuracy"], 0.5)
                self.assertTrue((root / "review_queue.csv").exists())
                source.write_text(source.read_text() + "\n")
                with self.assertRaisesRegex(ValueError, "input changed"):
                    evaluate_main()


if __name__ == "__main__":
    unittest.main()
