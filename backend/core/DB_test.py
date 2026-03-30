from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from core.MMR_rerank import mmr_rerank
except ModuleNotFoundError:
    try:
        from backend.core.MMR_rerank import mmr_rerank
    except ModuleNotFoundError:
        from MMR_rerank import mmr_rerank  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[2]
PERSIST_DIR = BASE_DIR / "backend" / "vector_store"
COLLECTION_NAME = "papers"

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
HYDE_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

DEFAULT_CANDIDATE_K = 100
DEFAULT_FINAL_K = 100
DEFAULT_MMR_LAMBDA = 0.7


@dataclass(frozen=True)
class SearchResources:
    collection: Any
    embedding_model: Any
    hyde_model: Any
    hyde_tokenizer: Any


def build_runtime_resources() -> SearchResources:
    """서버 시작 시 필요한 공용 리소스를 1회 생성합니다."""
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": device},
    )

    tokenizer = AutoTokenizer.from_pretrained(HYDE_MODEL_NAME)

    model_kwargs = {
        "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    hyde_model = AutoModelForCausalLM.from_pretrained(HYDE_MODEL_NAME, **model_kwargs)

    return SearchResources(
        collection=collection,
        embedding_model=embedding_model,
        hyde_model=hyde_model,
        hyde_tokenizer=tokenizer,
    )


class SearchService:
    """HyDE -> E5 -> Chroma -> MMR -> 응답 포맷 파이프라인 담당 서비스."""

    def __init__(self, resources: SearchResources):
        self.resources = resources

    def search(
        self,
        user_input: str,
        candidate_k: int = DEFAULT_CANDIDATE_K,
        final_k: int = DEFAULT_FINAL_K,
        lambda_param: float = DEFAULT_MMR_LAMBDA,
    ) -> list[dict]:
        normalized_input = user_input.strip()
        if not normalized_input:
            raise ValueError("user_input must not be empty")
        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than 0")
        if final_k <= 0:
            raise ValueError("final_k must be greater than 0")
        if not 0.0 <= lambda_param <= 1.0:
            raise ValueError("lambda_param must be between 0 and 1")

        generated_query = self._build_search_query(normalized_input)
        if not generated_query:
            return []
        
        print(f"[DEBUG] -------------------------------------------")
        print(f"[DEBUG] Generated HyDE Query:")
        print(f"{generated_query}")
        print(f"[DEBUG] -------------------------------------------")

        query_vector = self._create_query_vector(generated_query)

        candidate_items = self._search_papers(
            query_vector=query_vector,
            top_k=candidate_k,
        )
        if not candidate_items:
            return []

        final_recommendations = mmr_rerank(
            query_vector=query_vector,
            candidate_items=candidate_items,
            top_n=final_k,
            lambda_param=lambda_param,
        )

        return self._format_final_results(final_recommendations)

    def _build_search_query(self, user_input: str) -> str:
        """사용자 입력을 HyDE용 영문 초록으로 생성합니다."""
        prompt_content = f"""
당신은 HyDE 기반 학술 논문 검색을 돕는 도우미입니다.
사용자는 한국어 또는 영어로 입력할 수 있습니다.

사용자의 프로젝트 설명을 짧은 영문 연구 초록으로 다시 작성하세요.
조건:
1. 영문 문장만 출력합니다.
2. 2~3문장으로 작성합니다.
3. 암시된 구체적인 방법, 모델, 기술 용어가 있으면 포함합니다.
4. 글머리표, 라벨, 추가 설명은 출력하지 않습니다.

예시 입력: 군중이 많은 영상 장면에서 이상행동을 탐지하는 시스템
예시 출력: This paper presents a real-time video surveillance system for abnormal behavior detection in crowded environments. The approach combines spatiotemporal feature extraction with action recognition techniques to identify and classify anomalous human activities.

예시 입력: 최적의 대중교통 경로를 추천하는 서비스
예시 출력: We propose an intelligent route recommendation system for public transportation networks. The method leverages graph-based optimization and reinforcement learning to generate time-efficient and cost-effective itineraries from dynamic transit data.

사용자 입력: {user_input}
출력:
""".strip()

        tokenizer = self.resources.hyde_tokenizer
        model = self.resources.hyde_model

        messages = [{"role": "user", "content": prompt_content}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        model_inputs = tokenizer([text], return_tensors="pt")
        model_device = getattr(model, "device", None)
        if model_device is not None:
            model_inputs = {key: value.to(model_device) for key, value in model_inputs.items()}

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=150,
            temperature=0.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

        input_ids = model_inputs["input_ids"]
        generated_ids = [
            output_ids[len(input_id):]
            for input_id, output_ids in zip(input_ids, generated_ids)
        ]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response.strip()

    def _create_query_vector(self, query_text: str):
        formatted_query = f"query: {query_text}"
        return self.resources.embedding_model.embed_query(formatted_query)

    def _search_papers(self, query_vector, top_k: int) -> list[dict]:
        raw_results = self.resources.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances", "embeddings"],
        )
        return self._format_search_candidates(raw_results)

    @staticmethod
    def _normalize_categories(value: Any) -> list[str]:
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

    def _format_search_candidates(self, raw_results) -> list[dict]:
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
                    "id": str(doc_id),
                    "categories": self._normalize_categories(metadata_dict.get("categories")),
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

    def _format_final_results(self, results: list[dict]) -> list[dict]:
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
                
            update_date = item.get("update_date")
            if update_date is None:
                update_date = (item.get("metadata") or {}).get("update_date")

            formatted_results.append(
                {
                    "id": str(item.get("id", "")),
                    "similarity": similarity,
                    "categories": self._normalize_categories(categories),
                    "page_content": page_content,
                    "update_date": update_date,
                }
            )

        return formatted_results