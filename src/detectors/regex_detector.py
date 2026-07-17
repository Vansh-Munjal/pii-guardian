import re
from .base_detector import BaseDetector

PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
    "PHONE": r'(?:\+\s?\d{1,3}[\s\-]?)?\d{2,5}[\s\-]?\d{3,5}[\s\-]?\d{3,5}\b',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[\s\-]){3}\d{4}\b',
    "IP_ADDRESS": (
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    ),
    "DATE_OF_BIRTH": (
        r'\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}'
        r'|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}'
        r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}'
        r'|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b'
    ),
}


class RegexDetector(BaseDetector):
    def detect(self, text: str) -> list[dict]:
        entities = []
        for pii_type, pattern in PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matched_text = match.group().strip()
                if not matched_text:
                    continue
                entities.append({
                    "text": matched_text,
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.start() + len(matched_text),
                })
        return entities
