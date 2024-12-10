import json
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from ..utils.jsonl import save_documents_to_jsonl


class ChunkSplitter:
    def __init__(
        self,
        chunk_size: int,
    ) -> None:
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=int(0.15 * chunk_size)
        )

    def split(
        self, filepath: Path, splitter_config: Dict[str, Any]
    ) -> List[Document]:
        md_splitter = self._get_md_splitter(splitter_config)
        with open(filepath, "r") as f:
            filedata = f.read()
        documents = md_splitter.split_text(filedata)
        documents = self.text_splitter.split_documents(documents)
        return documents

    def _get_md_splitter(
        self, splitter_config: Dict[str, Any]
    ) -> MarkdownHeaderTextSplitter:
        return MarkdownHeaderTextSplitter(**splitter_config)

    def squeeze(self, documents: List[Document]) -> List[Document]:
        pass


def split_documents_by_dir(
    data_dir: Path,
    chunk_size: int = 1500,
) -> None:
    splitter = ChunkSplitter(chunk_size)
    chunks_meta = {}
    for files_dir in data_dir.iterdir():
        dirname = files_dir.name
        chunks_meta[dirname] = []
        splitter_config_path = list(files_dir.glob("*.json"))
        assert len(splitter_config_path) == 1
        with open(splitter_config_path[0], "r") as f:
            splitter_config = json.load(f)
        for filepath in files_dir.iterdir():
            if filepath.is_file() and filepath.suffix != ".json":
                chunks = splitter.split(filepath, splitter_config)
                chunks_meta[dirname].extend(chunks)
    return chunks_meta


def split_documents() -> None:
    """
    Split documents from /data/to_split directory to chunks
    and store it in /data/chunks
    """
    data_dir: Path = Path("./data/to_split")
    output_dir: Path = Path("./data/chunks")
    chunks_meta: Dict[str, List[Document]] = split_documents_by_dir(data_dir)
    for dirname, chunk_docs in chunks_meta.items():
        save_documents_to_jsonl(
            chunk_docs, str(output_dir / f"{dirname}.jsonl")
        )
    return None


if __name__ == "__main__":
    split_documents()
