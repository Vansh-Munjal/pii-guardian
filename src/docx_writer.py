import os
from docx.document import Document as DocumentType


def save_document(doc: DocumentType, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"Redacted document saved to: {output_path}")
