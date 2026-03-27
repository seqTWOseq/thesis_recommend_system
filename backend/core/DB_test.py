import os
from pathlib import Path

import chromadb
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from backend.core.query_trans import (
        generate_hypothetical_abstract,
        init_hyde_model,
    )
except ModuleNotFoundError:
    from query_trans import generate_hypothetical_abstract, init_hyde_model  # type: ignore

try:
    from backend.core.MMR_rerank import mmr_rerank
except ModuleNotFoundError:
    from MMR_rerank import mmr_rerank  # type: ignore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = Path(os.path.join(BASE_DIR, "backend", "vector_store"))
COLLECTION_NAME = "papers"
DEFAULT_CANDIDATE_K = 40
DEFAULT_FINAL_K = 5
DEFAULT_MMR_LAMBDA = 0.7


def init_search_system():
    """데이터베이스와 임베딩 모델, HyDE 모델을 메모리에 1회만 로드합니다."""
    print("검색 시스템 초기화 중... (ChromaDB, E5, HyDE, MMR)")

    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        model_kwargs={"device": device},
    )
    hyde_model, hyde_tokenizer = init_hyde_model()

    print(f"초기화 완료! ({collection.count()}개의 논문이 검색 준비 상태입니다.)\n")
    return collection, embedding_model, hyde_model, hyde_tokenizer


def build_search_query(user_input: str, hyde_model, hyde_tokenizer) -> str:
    """사용자 원문 입력을 HyDE 방식의 영문 초록으로 변환합니다."""
    return generate_hypothetical_abstract(user_input, hyde_model, hyde_tokenizer).strip()


def create_query_vector(query_text: str, embedding_model):
    """검색에 사용할 쿼리 벡터를 생성합니다."""
    formatted_query = f"query: {query_text}"
    return embedding_model.embed_query(formatted_query)


def format_search_candidates(raw_results) -> list[dict]:
    """Chroma 검색 결과를 후속 rerank 모듈이 쓰기 쉬운 리스트 구조로 정리합니다."""
    ids = raw_results.get("ids", [[]])[0]
    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    embeddings = raw_results.get("embeddings", [[]])[0]

    candidates = []
    for doc_id, document, metadata, distance, embedding in zip(
        ids,
        documents,
        metadatas,
        distances,
        embeddings,
    ):
        clean_document = document.replace("passage: ", "", 1) if isinstance(document, str) else ""
        distance_value = float(distance)
        similarity_value = 1.0 - distance_value

        candidates.append(
            {
                "id": doc_id,
                "document": clean_document,
                "metadata": metadata or {},
                "distance": distance_value,
                "similarity": similarity_value,
                "embedding": list(embedding) if embedding is not None else None,
            }
        )

    return candidates


def search_papers(query_vector, collection, top_k: int = DEFAULT_CANDIDATE_K):
    """입력 쿼리 벡터와 유사한 논문 후보를 ChromaDB에서 찾아 리스트 구조로 반환합니다."""
    raw_results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances", "embeddings"],
    )

    return format_search_candidates(raw_results)


def build_metadata_preview(metadata: dict) -> str:
    """출력용 메타데이터 미리보기를 생성합니다."""
    if not isinstance(metadata, dict) or not metadata:
        return "{}"

    preview_keys = ["categories", "update_date"]
    preview_parts = []

    for key in preview_keys:
        if key in metadata:
            preview_parts.append(f"{key}={metadata[key]}")

    if not preview_parts:
        preview_parts = [f"{key}={value}" for key, value in list(metadata.items())[:2]]

    return ", ".join(preview_parts)


def print_final_recommendations(recommendations: list[dict]):
    """최종 추천 결과만 요약해서 출력합니다."""
    if not recommendations:
        print("출력할 최종 추천 결과가 없습니다.")
        return

    print("\n최종 추천 결과:")
    for item in recommendations:
        metadata = item.get("metadata", {})
        document_text = item.get("document", "")

        print("-" * 60)
        print(f"MMR 순위: {item.get('mmr_rank')}")
        print(f"논문 ID: {item.get('id')}")
        print(f"유사도: {item.get('similarity', 0.0):.4f}")
        print(f"MMR 점수: {item.get('mmr_score', 0.0):.4f}")
        print(f"메타데이터: {build_metadata_preview(metadata)}")
        print(f"본문:\n{document_text}")


def print_pre_rerank_top5(candidates: list[dict], top_k: int = DEFAULT_FINAL_K):
    """MMR 적용 전 유사도 기준 상위 후보를 출력합니다."""
    if not candidates:
        print("출력할 사전 후보 결과가 없습니다.")
        return

    preview_items = candidates[:top_k]
    print("\nMMR 적용 전 유사도 기준 상위 결과:")

    for rank, item in enumerate(preview_items, start=1):
        metadata = item.get("metadata", {})
        document_text = item.get("document", "")

        print("-" * 60)
        print(f"사전 순위: {rank}")
        print(f"논문 ID: {item.get('id')}")
        print(f"유사도: {item.get('similarity', 0.0):.4f}")
        print(f"메타데이터: {build_metadata_preview(metadata)}")
        print(f"본문:\n{document_text}")


if __name__ == "__main__":
    db_collection, embedding_model, hyde_model, hyde_tokenizer = init_search_system()

    print("=" * 60)
    print("AI 논문 검색 및 MMR 추천 테스트")
    print("종료하려면 'q', 'quit', 'exit' 중 하나를 입력하세요.")
    print("=" * 60)

    while True:
        user_input = input("\n프로젝트 주제를 입력하세요: ").strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            print("검색 테스트를 종료합니다.")
            break

        if not user_input:
            print("검색할 주제를 입력해주세요.")
            continue

        print("\n1. HyDE 쿼리를 생성하는 중...")
        generated_query = build_search_query(user_input, hyde_model, hyde_tokenizer)

        if not generated_query:
            print("HyDE 모델이 빈 쿼리를 반환했습니다. 다시 시도해주세요.")
            continue

        print("-" * 60)
        print(f"[사용자 원문 입력]\n{user_input}")
        print("-" * 60)
        print(f"[HyDE 생성 영문 초록]\n{generated_query}")
        print("-" * 60)

        print("\n2. 쿼리 벡터를 생성하는 중...")
        query_vector = create_query_vector(generated_query, embedding_model)

        print("\n3. ChromaDB에서 후보 논문 40개를 검색하는 중...")
        search_candidates = search_papers(
            query_vector,
            db_collection,
            top_k=DEFAULT_CANDIDATE_K,
        )

        candidate_count = len(search_candidates)
        print(f"후보 개수: {candidate_count}")

        if not search_candidates:
            print("일치하는 검색 결과가 없습니다.")
            continue

        print_pre_rerank_top5(search_candidates, top_k=DEFAULT_FINAL_K)

        print("\n4. MMR로 최종 추천 5개를 재정렬하는 중...")
        final_recommendations = mmr_rerank(
            query_vector=query_vector,
            candidate_items=search_candidates,
            top_n=DEFAULT_FINAL_K,
            lambda_param=DEFAULT_MMR_LAMBDA,
        )

        final_count = len(final_recommendations)
        print(f"최종 추천 개수: {final_count}")

        if not final_recommendations:
            print("MMR 재정렬 결과가 없습니다.")
            continue

        print_final_recommendations(final_recommendations)
        print("\n결과 출력을 완료하여 프로그램을 종료합니다.")
        break
