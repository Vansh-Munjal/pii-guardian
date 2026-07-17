import argparse
import json
import os

from src.docx_reader import load_document, iter_paragraphs
from src.detectors import RegexDetector, NERDetector
from src.replacement_engine import redact_paragraph
from src.docx_writer import save_document
from src import fake_generator
from src import evaluator

INPUT_PATH        = "input/red_herring_prospectus.docx"
OUTPUT_PATH       = "output/redacted_prospectus.docx"
GROUND_TRUTH_PATH = "tests/ground_truth.json"
REPORT_PATH       = "output/evaluation_report.json"


def build_detectors() -> list:
    print("Loading detectors...")
    regex = RegexDetector()
    ner   = NERDetector()
    print("  ✓ Regex detector ready")
    print("  ✓ NER detector ready (en_core_web_lg)")
    return [regex, ner]


def run_redaction(input_path: str, output_path: str, detectors: list) -> list[dict]:
    doc = load_document(input_path)
    all_detected = []

    paragraphs = list(iter_paragraphs(doc))
    print(f"\nProcessing {len(paragraphs)} paragraphs...")

    for paragraph in paragraphs:
        full_text = "".join(run.text for run in paragraph.runs)
        if not full_text.strip():
            continue

        for detector in detectors:
            all_detected.extend(detector.detect(full_text))

        redact_paragraph(paragraph, detectors)

    save_document(doc, output_path)
    return all_detected


def run_evaluation(all_detected: list[dict], ground_truth_path: str, report_path: str) -> None:
    try:
        truth = evaluator.load_ground_truth(ground_truth_path)
    except FileNotFoundError:
        print(f"\nNo ground truth file found at {ground_truth_path}. Skipping evaluation.")
        return

    results = evaluator.evaluate(all_detected, truth)
    evaluator.print_report(results)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Evaluation report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="PII Redaction Tool")
    parser.add_argument("--input",        default=INPUT_PATH,        help="Path to input DOCX")
    parser.add_argument("--output",       default=OUTPUT_PATH,       help="Path to save redacted DOCX")
    parser.add_argument("--evaluate",     action="store_true",       help="Run evaluation against ground truth")
    parser.add_argument("--ground-truth", default=GROUND_TRUTH_PATH, help="Path to ground truth JSON")
    parser.add_argument("--report",       default=REPORT_PATH,       help="Path to save evaluation report JSON")
    args = parser.parse_args()

    detectors = build_detectors()
    fake_generator.reset_cache()

    all_detected = run_redaction(args.input, args.output, detectors)

    print(f"\nTotal PII instances detected: {len(all_detected)}")
    print(f"Unique PII values replaced:   {len(set(e['text'] for e in all_detected))}")

    if args.evaluate:
        run_evaluation(all_detected, args.ground_truth, args.report)


if __name__ == "__main__":
    main()

