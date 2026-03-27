from __future__ import annotations

from typing import Any

import numpy as np


def _to_numpy_vector(vector: Any) -> np.ndarray | None:
    """입력 벡터를 1차원 numpy 배열로 변환합니다."""
    if vector is None:
        return None

    try:
        array = np.asarray(vector, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError):
        return None

    if array.size == 0:
        return None

    return array


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """두 벡터 간 cosine similarity를 계산합니다."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def _prepare_candidates(candidate_items: list[dict]) -> list[dict]:
    """유효한 embedding이 포함된 후보만 선별해 내부 계산용 구조로 정리합니다."""
    prepared_candidates = []

    for item in candidate_items:
        if not isinstance(item, dict):
            continue

        embedding = _to_numpy_vector(item.get("embedding"))
        if embedding is None:
            continue

        prepared_candidates.append(
            {
                "item": item,
                "embedding": embedding,
            }
        )

    return prepared_candidates


def mmr_rerank(
    query_vector,
    candidate_items,
    top_n: int = 10,
    lambda_param: float = 0.7,
):
    """후보 논문 리스트를 MMR 기준으로 재정렬하여 상위 결과를 반환합니다."""
    if top_n <= 0:
        return []

    if not 0.0 <= lambda_param <= 1.0:
        raise ValueError("lambda_param은 0과 1 사이의 값이어야 합니다.")

    query_array = _to_numpy_vector(query_vector)
    if query_array is None:
        raise ValueError("query_vector가 비어 있거나 올바르지 않습니다.")

    if not isinstance(candidate_items, list):
        raise ValueError("candidate_items는 list[dict] 형태여야 합니다.")

    prepared_candidates = _prepare_candidates(candidate_items)
    if not prepared_candidates:
        return []

    valid_candidates = []
    for candidate in prepared_candidates:
        candidate_vector = candidate["embedding"]

        if candidate_vector.shape != query_array.shape:
            continue

        relevance_score = _cosine_similarity(query_array, candidate_vector)
        valid_candidates.append(
            {
                "item": candidate["item"],
                "embedding": candidate_vector,
                "relevance": relevance_score,
            }
        )

    if not valid_candidates:
        return []

    selected_items = []
    remaining_items = valid_candidates.copy()
    final_count = min(top_n, len(remaining_items))

    first_item = max(remaining_items, key=lambda item: item["relevance"])
    remaining_items.remove(first_item)

    first_result = dict(first_item["item"])
    first_result["mmr_rank"] = 1
    first_result["mmr_score"] = first_item["relevance"]
    selected_items.append(
        {
            "result": first_result,
            "embedding": first_item["embedding"],
            "relevance": first_item["relevance"],
        }
    )

    while len(selected_items) < final_count and remaining_items:
        best_candidate = None
        best_mmr_score = -np.inf

        for candidate in remaining_items:
            diversity_score = max(
                _cosine_similarity(candidate["embedding"], selected["embedding"])
                for selected in selected_items
            )

            mmr_score = (lambda_param * candidate["relevance"]) - (
                (1.0 - lambda_param) * diversity_score
            )

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = candidate

        if best_candidate is None:
            break

        remaining_items.remove(best_candidate)

        result_item = dict(best_candidate["item"])
        result_item["mmr_rank"] = len(selected_items) + 1
        result_item["mmr_score"] = float(best_mmr_score)
        selected_items.append(
            {
                "result": result_item,
                "embedding": best_candidate["embedding"],
                "relevance": best_candidate["relevance"],
            }
        )

    return [selected["result"] for selected in selected_items]
