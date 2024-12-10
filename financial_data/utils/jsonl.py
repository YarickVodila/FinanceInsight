import json
from typing import List

from langchain_core.documents import Document


def save_documents_to_jsonl(documents: List[Document], file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as jsonl_file:
        for doc in documents:
            jsonl_file.write(doc.model_dump_json() + "\n")
    return None


def load_documents_from_jsonl(file_path: str) -> List[Document]:
    documents = []
    with open(file_path, "r", encoding="utf-8") as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            document = Document(**data)
            documents.append(document)
    return documents
