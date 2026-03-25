from __future__ import annotations

from pathlib import Path
from pprint import pprint
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection


PERSIST_DIR = Path("backend/vector_store")
DATA_PATH = PERSIST_DIR / "arxiv_final.json"
COLLECTION_NAME = "papers"


def load_vector_db_dataframe_builder():
    """Import the storage-only embedding pipeline entrypoint."""
    try:
        from backend.core.embedding import build_vector_db_dataframe
    except ModuleNotFoundError:
        from embedding import build_vector_db_dataframe  # type: ignore

    return build_vector_db_dataframe


def get_chroma_client() -> chromadb.PersistentClient:
    """Create a persistent Chroma client under backend/vector_store."""
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(PERSIST_DIR))


def get_or_create_collection() -> Collection:
    """Return the Chroma collection that stores article embeddings."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Article embeddings created by backend.core.embedding",
            "source_file": str(DATA_PATH),
        },
    )


def has_value(value: Any) -> bool:
    """Treat None and NaN as missing values."""
    return value is not None and value == value


def strip_passage_prefix(text: str) -> str:
    """Remove the E5 storage prefix from a document before saving it."""
    prefix = "passage: "
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def build_chroma_records(df_vector_db) -> list[dict[str, Any]]:
    """Convert the embedding DataFrame to Chroma records."""
    records: list[dict[str, Any]] = []

    for _, row in df_vector_db.iterrows():
        metadata: dict[str, Any] = {}

        if has_value(row.get("update_date")):
            metadata["update_date"] = int(row["update_date"])
        if has_value(row.get("categories")):
            metadata["categories"] = str(row["categories"])

        records.append(
            {
                "id": str(row["id"]),
                "document": strip_passage_prefix(str(row["page_content"])),
                "metadata": metadata,
                "embedding": list(row["vector"]),
            }
        )

    return records


def upsert_records_to_chroma(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Store embedding records in Chroma and read back a preview."""
    if not records:
        raise ValueError("No records to upsert.")

    collection = get_or_create_collection()

    collection.upsert(
        ids=[record["id"] for record in records],
        documents=[record["document"] for record in records],
        metadatas=[record["metadata"] for record in records],
        embeddings=[record["embedding"] for record in records],
    )

    stored = collection.get(
        ids=[record["id"] for record in records],
        include=["documents", "metadatas", "embeddings"],
    )

    first_embedding = stored["embeddings"][0]

    return {
        "collection_name": collection.name,
        "collection_count": collection.count(),
        "stored_preview": {
            "id": stored["ids"][0],
            "document_preview": stored["documents"][0][:160],
            "metadata": stored["metadatas"][0],
            "embedding_dimension": len(first_embedding),
            "embedding_preview": list(first_embedding[:8]),
        },
    }


def seed_chroma_from_embedding_pipeline(
    file_path: Path = DATA_PATH,
    nrows: int = 10,
) -> dict[str, Any]:
    """Build the storage DataFrame in embedding.py and save it to Chroma."""
    build_vector_db_dataframe = load_vector_db_dataframe_builder()
    df_vector_db = build_vector_db_dataframe(str(file_path), nrows=nrows)
    records = build_chroma_records(df_vector_db)
    stored_result = upsert_records_to_chroma(records)

    first_record = records[0]

    return {
        "rows_prepared": len(records),
        "dataframe_columns": list(df_vector_db.columns),
        "embedding_result_preview": {
            "id": first_record["id"],
            "document_preview": first_record["document"][:160],
            "metadata": first_record["metadata"],
            "embedding_dimension": len(first_record["embedding"]),
            "embedding_preview": first_record["embedding"][:8],
        },
        "stored_result": stored_result,
    }


if __name__ == "__main__":
    pprint(seed_chroma_from_embedding_pipeline())
