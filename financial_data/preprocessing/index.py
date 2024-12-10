import os
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.faiss import DistanceStrategy

from ..utils.jsonl import load_documents_from_jsonl


def index_chunks() -> None:
    """
    Indexing chunks in directory and save it to FAISS database
    """
    input_dir = Path("./data/chunks")
    output_dir = Path("./data/index")
    os.makedirs(output_dir, exist_ok=True)

    model_path = "intfloat/multilingual-e5-small"
    embeddings = HuggingFaceEmbeddings(
        model_name=model_path,
        multi_process=True,
        encode_kwargs={"normalize_embeddings": True},
    )

    documents = []
    for filepath in input_dir.iterdir():
        if filepath.is_file() and filepath.suffix == ".jsonl":
            documents.extend(load_documents_from_jsonl(filepath))

    faiss_cosine = FAISS.from_documents(
        documents, embeddings, distance_strategy=DistanceStrategy.COSINE
    )
    faiss_cosine.save_local(str(output_dir))
    return None


if __name__ == "__main__":
    index_chunks()
