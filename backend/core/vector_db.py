from __future__ import annotations

import os
from pathlib import Path
from pprint import pprint
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = Path(os.path.join(BASE_DIR, "backend", "vector_store"))
DATA_PATH = Path(os.path.join(BASE_DIR, "data_pipeline", "processed_data", "arXiv_final.json"))
COLLECTION_NAME = "papers"


def load_vector_db_dataframe_builder():
    """저장 전용 임베딩 파이프라인의 진입점(entrypoint)을 가져옵니다."""
    try:
        from backend.core.embedding import build_vector_db_dataframe
    except ModuleNotFoundError:
        from embedding import build_vector_db_dataframe  # type: ignore

    return build_vector_db_dataframe


def get_chroma_client() -> chromadb.PersistentClient:
    """backend/vector_store 경로에 영구적인(persistent) 크로마(Chroma) 클라이언트를 생성합니다."""
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(PERSIST_DIR))

def reset_and_get_collection() -> Collection:
    """기존 컬렉션이 존재할 경우 삭제하고, 새로운 컬렉션을 생성하여 반환합니다."""
    client = get_chroma_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"기존 데이터 초기화 완료: '{COLLECTION_NAME}' 컬렉션 삭제됨")
    except Exception:
        print(f"삭제할 기존 컬렉션이 없습니다. 새로 생성합니다.")
        
    return client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            # 핵심 설정: 유클리드 거리(l2) 대신 코사인 유사도(cosine)를 사용하도록 지정
            "hnsw:space": "cosine", 
            "description": "코사인 유사도 기반의 논문 임베딩 컬렉션",
            "source_file": str(DATA_PATH),
        },
    )
    
def has_value(value: Any) -> bool:
    """None과 NaN을 결측치로 취급하여 판별합니다."""
    return value is not None and value == value

def strip_passage_prefix(text: str) -> str:
    """문서를 저장하기 전에 E5 모델의 저장용 접두사('passage: ')를 제거합니다."""
    prefix = "passage: "
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text

def build_chroma_records(df_vector_db) -> list[dict[str, Any]]:
    """임베딩 데이터프레임을 크로마(Chroma) 레코드 형식으로 변환합니다."""
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

def upsert_records_to_chroma(records: list[dict[str, Any]], batch_size: int = 5000) -> dict[str, Any]:
    """메모리 제한을 방지하기 위해 배치(batch) 단위로 임베딩 레코드를 크로마에 저장(upsert)합니다."""
    if not records:
        raise ValueError("저장할 레코드가 없습니다.")

    collection = reset_and_get_collection()
    total_records = len(records)
    
    print(f"총 {total_records}개의 레코드 저장을 시작합니다. (배치 크기: {batch_size})")

    # ChromaDB 제한을 피하기 위한 배치 분할 저장
    for i in range(0, total_records, batch_size):
        batch = records[i : i + batch_size]
        collection.upsert(
            ids=[record["id"] for record in batch],
            documents=[record["document"] for record in batch],
            metadatas=[record["metadata"] for record in batch],
            embeddings=[record["embedding"] for record in batch],
        )
        print(f" - 진행 상황: {min(i + batch_size, total_records)} / {total_records} 저장 완료")

    # 확인을 위해 첫 번째 데이터 조회
    stored = collection.get(
        ids=[records[0]["id"]],
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
    nrows: int | None = None, # None으로 설정 시 전체 데이터 로드
) -> dict[str, Any]:
    """embedding.py에서 저장용 데이터프레임을 생성하고 이를 크로마에 저장합니다."""
    build_vector_db_dataframe = load_vector_db_dataframe_builder()
    
    # nrows가 지정되지 않으면 전체 데이터를 읽어오도록 매개변수 전달
    kwargs = {"nrows": nrows} if nrows is not None else {}
    df_vector_db = build_vector_db_dataframe(str(file_path), **kwargs)
    
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
    # nrows 매개변수를 제외하여 약 53만개의 전체 데이터를 처리합니다.
    pprint(seed_chroma_from_embedding_pipeline())
