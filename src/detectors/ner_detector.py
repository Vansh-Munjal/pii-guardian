import re
import spacy
from .base_detector import BaseDetector

LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG":    "ORG",
    "GPE":    "ADDRESS",
    "LOC":    "ADDRESS",
    "FAC":    "ADDRESS",
}

_FALSE_POSITIVE_PATTERN = re.compile(
    r'^(\d+\w*|[A-Z]\d+|\w+\s+(Floor|Road|Table|Section|Clause|Annex|Schedule|Exhibit|No\.?|Sr\.?))$',
    re.IGNORECASE,
)


def _is_valid_entity(text: str, pii_type: str) -> bool:
    text = text.strip()

    if len(text) < 3:
        return False

    if re.fullmatch(r'[\d\W]+', text):
        return False

    if _FALSE_POSITIVE_PATTERN.match(text):
        return False

    if pii_type == "PERSON":
        words = text.split()
        if not any(re.fullmatch(r'[A-Za-z]{2,}', w) for w in words):
            return False

    return True


class NERDetector(BaseDetector):
    def __init__(self, model: str = "en_core_web_lg"):
        self.nlp = spacy.load(model)

    def detect(self, text: str) -> list[dict]:
        if not text.strip():
            return []

        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ not in LABEL_MAP:
                continue
            pii_type = LABEL_MAP[ent.label_]
            entity_text = ent.text.strip()
            if not _is_valid_entity(entity_text, pii_type):
                continue
            entities.append({
                "text":  entity_text,
                "type":  pii_type,
                "start": ent.start_char,
                "end":   ent.end_char,
            })
        return entities
