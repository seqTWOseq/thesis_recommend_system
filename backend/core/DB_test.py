from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from core.MMR_rerank import mmr_rerank
    from core.query_trans import (
        generate_hypothetical_abstract,
        init_hyde_model,
    )
except ModuleNotFoundError:
    try:
        from backend.core.MMR_rerank import mmr_rerank
        from backend.core.query_trans import (
            generate_hypothetical_abstract,
            init_hyde_model,
        )
    except ModuleNotFoundError:
        from MMR_rerank import mmr_rerank  # type: ignore
        from query_trans import generate_hypothetical_abstract, init_hyde_model  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[2]
PERSIST_DIR = BASE_DIR / "backend" / "vector_store"
COLLECTION_NAME = "papers"
DEFAULT_CANDIDATE_K = 100
DEFAULT_FINAL_K = 100
DEFAULT_PREVIEW_K = 5
DEFAULT_MMR_LAMBDA = 0.7


@lru_cache(maxsize=1)
def init_search_system():
    """Load and cache Chroma, embedding model, and HyDE model."""
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        model_kwargs={"device": device},
    )
    hyde_model, hyde_tokenizer = init_hyde_model()

    return collection, embedding_model, hyde_model, hyde_tokenizer


def build_search_query(user_input: str, hyde_model, hyde_tokenizer) -> str:
    """Convert user input into a HyDE-generated English abstract."""
    return generate_hypothetical_abstract(user_input, hyde_model, hyde_tokenizer).strip()


def create_query_vector(query_text: str, embedding_model):
    """Create an E5 query embedding."""
    formatted_query = f"query: {query_text}"
    return embedding_model.embed_query(formatted_query)


def _normalize_categories(value: Any) -> list[str]:
    """Normalize categories into a JSON-friendly list[str]."""
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]

    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return []

        try:
            parsed_value = ast.literal_eval(stripped_value)
        except (ValueError, SyntaxError):
            parsed_value = None

        if isinstance(parsed_value, (list, tuple, set)):
            return [str(item) for item in parsed_value if str(item)]

        if "," in stripped_value:
            return [item.strip() for item in stripped_value.split(",") if item.strip()]

        return [stripped_value]

    return [str(value)]


def format_search_candidates(raw_results) -> list[dict]:
    """Convert Chroma query output into a JSON-friendly list of candidates."""
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
        metadata_dict = metadata or {}
        clean_document = document.replace("passage: ", "", 1) if isinstance(document, str) else ""
        distance_value = float(distance)
        similarity_value = 1.0 - distance_value

        candidates.append(
            {
                "id": doc_id,
                "categories": _normalize_categories(metadata_dict.get("categories")),
                "document": clean_document,
                "page_content": clean_document,
                "metadata": metadata_dict,
                "distance": distance_value,
                "similarity": similarity_value,
                "score": similarity_value,
                "embedding": list(embedding) if embedding is not None else None,
            }
        )

    return candidates


def search_papers(query_vector, collection, top_k: int = DEFAULT_CANDIDATE_K):
    """Search top-k Chroma candidates using the query vector."""
    raw_results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances", "embeddings"],
    )
    return format_search_candidates(raw_results)


def _run_search_pipeline_steps(
    user_input: str,
    candidate_k: int = DEFAULT_CANDIDATE_K,
    final_k: int = DEFAULT_FINAL_K,
) -> dict[str, Any]:
    """Run the full pipeline and keep intermediate values for CLI inspection."""
    normalized_input = user_input.strip()
    if not normalized_input or candidate_k <= 0 or final_k <= 0:
        return {
            "user_input": normalized_input,
            "generated_query": "",
            "query_vector": [],
            "candidate_items": [],
            "final_recommendations": [],
        }

    collection, embedding_model, hyde_model, hyde_tokenizer = init_search_system()

    generated_query = build_search_query(normalized_input, hyde_model, hyde_tokenizer)
    if not generated_query:
        return {
            "user_input": normalized_input,
            "generated_query": "",
            "query_vector": [],
            "candidate_items": [],
            "final_recommendations": [],
        }

    query_vector = create_query_vector(generated_query, embedding_model)
    candidate_items = search_papers(
        query_vector,
        collection,
        top_k=candidate_k,
    )

    if not candidate_items:
        return {
            "user_input": normalized_input,
            "generated_query": generated_query,
            "query_vector": query_vector,
            "candidate_items": [],
            "final_recommendations": [],
        }

    final_recommendations = mmr_rerank(
        query_vector=query_vector,
        candidate_items=candidate_items,
        top_n=final_k,
        lambda_param=DEFAULT_MMR_LAMBDA,
    )

    return {
        "user_input": normalized_input,
        "generated_query": generated_query,
        "query_vector": query_vector,
        "candidate_items": candidate_items,
        "final_recommendations": final_recommendations,
    }


def format_final_results(results: list[dict]) -> list[dict]:
    """Reduce reranked results to the final API response schema."""
    formatted_results = []

    for item in results:
        if not isinstance(item, dict):
            continue

        similarity_value = item.get("similarity", 0.0)
        try:
            similarity = round(float(similarity_value), 4)
        except (TypeError, ValueError):
            similarity = 0.0

        categories = item.get("categories")
        if categories is None:
            categories = (item.get("metadata") or {}).get("categories")

        page_content = item.get("page_content")
        if not isinstance(page_content, str) or not page_content:
            document_value = item.get("document", "")
            page_content = document_value if isinstance(document_value, str) else ""

        formatted_results.append(
            {
                "id": str(item.get("id", "")),
                "similarity": similarity,
                "categories": _normalize_categories(categories),
                "page_content": page_content,
            }
        )

    return formatted_results


def run_search_pipeline(
    user_input: str,
    candidate_k: int = DEFAULT_CANDIDATE_K,
    final_k: int = DEFAULT_FINAL_K,
) -> list[dict]:
    """Run HyDE -> embedding -> Chroma -> MMR and return final results."""
    search_result = _run_search_pipeline_steps(
        user_input=user_input,
        candidate_k=candidate_k,
        final_k=final_k,
    )
    return format_final_results(search_result["final_recommendations"])


def build_metadata_preview(metadata: dict) -> str:
    """Create a short metadata preview string for CLI output."""
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
    """Print final reranked recommendations for manual testing."""
    if not recommendations:
        print("No final recommendations were produced.")
        return

    print("\nFinal recommendations:")
    for item in recommendations:
        metadata = item.get("metadata", {})
        document_text = item.get("document", "")

        print("-" * 60)
        print(f"MMR rank: {item.get('mmr_rank')}")
        print(f"Paper ID: {item.get('id')}")
        print(f"Similarity: {item.get('similarity', 0.0):.4f}")
        print(f"MMR score: {item.get('mmr_score', 0.0):.4f}")
        print(f"Metadata: {build_metadata_preview(metadata)}")
        print(f"Content:\n{document_text}")


def print_pre_rerank_top5(candidates: list[dict], top_k: int = DEFAULT_PREVIEW_K):
    """Print the top candidates before MMR reranking for manual testing."""
    if not candidates:
        print("No candidate results were produced.")
        return

    preview_items = candidates[:top_k]
    print("\nTop candidates before MMR:")

    for rank, item in enumerate(preview_items, start=1):
        metadata = item.get("metadata", {})
        document_text = item.get("document", "")

        print("-" * 60)
        print(f"Candidate rank: {rank}")
        print(f"Paper ID: {item.get('id')}")
        print(f"Similarity: {item.get('similarity', 0.0):.4f}")
        print(f"Metadata: {build_metadata_preview(metadata)}")
        print(f"Content:\n{document_text}")


if __name__ == "__main__":
    print("=" * 60)
    print("AI paper search and MMR rerank test")
    print("Enter 'q', 'quit', or 'exit' to stop")
    print("=" * 60)

    print("\nLoading search system...")
    collection, _, _, _ = init_search_system()
    print(f"Ready. Collection size: {collection.count()}")

    while True:
        user_input = input("\nEnter a project topic: ").strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            print("Search test ended.")
            break

        if not user_input:
            print("Please enter a topic to search.")
            continue

        print("\nRunning search pipeline...")
        search_result = _run_search_pipeline_steps(
            user_input=user_input,
            candidate_k=DEFAULT_CANDIDATE_K,
            final_k=DEFAULT_FINAL_K,
        )

        generated_query = search_result["generated_query"]
        candidate_items = search_result["candidate_items"]
        final_recommendations = search_result["final_recommendations"]

        if not generated_query:
            print("HyDE returned an empty query. Try a different input.")
            continue

        print("-" * 60)
        print(f"[User input]\n{user_input}")
        print("-" * 60)
        print(f"[HyDE abstract]\n{generated_query}")
        print("-" * 60)
        print(f"Candidate count: {len(candidate_items)}")
        print(f"Final recommendation count: {len(final_recommendations)}")

        if not candidate_items:
            print("No matching candidates were found.")
            continue

        print_pre_rerank_top5(candidate_items, top_k=DEFAULT_PREVIEW_K)
        print_final_recommendations(final_recommendations)
