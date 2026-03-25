from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection


PERSIST_DIR = Path("backend/vector_store")
COLLECTION_NAME = "papers"


def get_chroma_client() -> chromadb.PersistentClient:
    """
    로컬 디렉터리에 저장되는 Chroma PersistentClient 생성
    """
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    return client


def get_or_create_collection() -> Collection:
    """
    papers 컬렉션을 가져오거나 없으면 생성
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "thesis recommendation empty test collection"},
    )
    return collection


def create_empty_collection_test() -> dict[str, Any]:
    """
    로컬 설치 및 빈 컬렉션 생성 테스트용
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "thesis recommendation empty test collection"},
    )

    return {
        "ok": True,
        "persist_dir": str(PERSIST_DIR),
        "collection_name": collection.name,
        "collection_count": collection.count(),
        "all_collections": client.list_collections(),
    }