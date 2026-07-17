import json
from collections import defaultdict


def _normalize(text: str) -> str:
    return text.strip().lower()


def evaluate(detected: list[dict], ground_truth: list[dict]) -> dict:
    """
    Compares detected entities against hand-labeled ground truth.

    Both lists contain dicts with at least {"text": ..., "type": ...}.
    Matching is done by normalized text + type. Position is ignored because
    detectors may return slightly different offsets.

    Returns per-type and overall Precision, Recall, and F1.
    """
    detected_set = defaultdict(set)
    for e in detected:
        key = (_normalize(e["text"]), e["type"])
        detected_set[e["type"]].add(key)

    truth_set = defaultdict(set)
    for e in ground_truth:
        key = (_normalize(e["text"]), e["type"])
        truth_set[e["type"]].add(key)

    all_types = set(detected_set) | set(truth_set)
    results = {}

    total_tp = total_fp = total_fn = 0

    for pii_type in sorted(all_types):
        detected_keys = detected_set.get(pii_type, set())
        truth_keys = truth_set.get(pii_type, set())

        tp = len(detected_keys & truth_keys)
        fp = len(detected_keys - truth_keys)
        fn = len(truth_keys - detected_keys)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        results[pii_type] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall":    round(recall, 4),
            "f1":        round(f1, 4),
        }

        total_tp += tp
        total_fp += fp
        total_fn += fn

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall    = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1        = (2 * overall_precision * overall_recall /
                         (overall_precision + overall_recall)
                         if (overall_precision + overall_recall) > 0 else 0.0)

    results["OVERALL"] = {
        "tp": total_tp, "fp": total_fp, "fn": total_fn,
        "precision": round(overall_precision, 4),
        "recall":    round(overall_recall, 4),
        "f1":        round(overall_f1, 4),
    }

    return results


def load_ground_truth(path: str) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


def print_report(results: dict) -> None:
    print(f"\n{'─'*60}")
    print(f"{'PII TYPE':<20} {'PRECISION':>10} {'RECALL':>10} {'F1':>10}")
    print(f"{'─'*60}")
    for pii_type, metrics in results.items():
        if pii_type == "OVERALL":
            continue
        print(f"{pii_type:<20} {metrics['precision']:>10.4f} {metrics['recall']:>10.4f} {metrics['f1']:>10.4f}")
    print(f"{'─'*60}")
    o = results["OVERALL"]
    print(f"{'OVERALL':<20} {o['precision']:>10.4f} {o['recall']:>10.4f} {o['f1']:>10.4f}")
    print(f"{'─'*60}\n")
