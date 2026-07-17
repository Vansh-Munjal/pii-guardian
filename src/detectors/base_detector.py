from abc import ABC, abstractmethod


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> list[dict]:
        """
        Returns a list of detected PII entities.
        Each entity is a dict with keys:
            - text  : the original matched string
            - type  : PII category (e.g. "EMAIL", "PERSON")
            - start : character start index in the input text
            - end   : character end index in the input text
        """
        pass
