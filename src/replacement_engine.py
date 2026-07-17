from docx.text.paragraph import Paragraph
from src.detectors.base_detector import BaseDetector
from src import fake_generator


def _build_replacement_map(text: str, detectors: list[BaseDetector]) -> dict[str, str]:
    all_entities = []
    for detector in detectors:
        all_entities.extend(detector.detect(text))

    all_entities.sort(key=lambda e: (e["start"], -len(e["text"])))

    replacement_map = {}
    last_end = -1
    for entity in all_entities:
        if entity["start"] < last_end:
            continue
        original = entity["text"]
        if original and original not in replacement_map:
            replacement_map[original] = fake_generator.get_fake(original, entity["type"])
        last_end = entity["end"]

    return replacement_map


def _apply_to_text(text: str, replacement_map: dict[str, str]) -> str:
    for original in sorted(replacement_map, key=len, reverse=True):
        text = text.replace(original, replacement_map[original])
    return text


def redact_paragraph(paragraph: Paragraph, detectors: list[BaseDetector]) -> None:
    if not paragraph.runs:
        return

    full_text = "".join(run.text for run in paragraph.runs)
    if not full_text.strip():
        return

    replacement_map = _build_replacement_map(full_text, detectors)
    if not replacement_map:
        return

    new_text = _apply_to_text(full_text, replacement_map)
    if new_text == full_text:
        return

    paragraph.runs[0].text = new_text
    for run in paragraph.runs[1:]:
        run.text = ""

