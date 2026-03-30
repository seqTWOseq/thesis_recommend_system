from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import time
import torch


router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., description="사용자 검색어")
    top_k: int = Field(100, ge=1, le=300, description="최종 반환 개수")
    candidate_k: int | None = Field(
        None,
        ge=1,
        le=1000,
        description="MMR 전 후보 개수. 비우면 max(top_k, 100) 사용",
    )
    lambda_param: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="MMR relevance/diversity 가중치",
    )


class PaperResult(BaseModel):
    id: str
    similarity: float
    categories: list[str]
    page_content: str


class SearchResponse(BaseModel):
    results: list[PaperResult]


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}


@router.post("/api/search", response_model=SearchResponse)
def search(request: Request, payload: SearchRequest):
    normalized_query = payload.query.strip()
    if not normalized_query:
        raise HTTPException(status_code=400, detail="query must not be empty")

    search_service = getattr(request.app.state, "search_service", None)
    if search_service is None:
        raise HTTPException(status_code=503, detail="search service is not initialized")

    candidate_k = payload.candidate_k if payload.candidate_k is not None else max(payload.top_k, 100)

    # ------------------- 디버깅 로그 시작 -------------------
    start_time = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"\n[DEBUG] ===========================================")
    print(f"[DEBUG] 검색 요청 수신: '{normalized_query}'")
    print(f"[DEBUG] 구동 환경(Device): {device.upper()}")
    if device == "cuda":
        print(f"[DEBUG] GPU 모델명: {torch.cuda.get_device_name(0)}")
    print(f"[DEBUG] 설정값 - 후보 수(candidate_k): {candidate_k}, 반환 수(top_k): {payload.top_k}")
    print(f"[DEBUG] 검색 파이프라인 연산 시작...")
    # --------------------------------------------------------

    try:
        step_start = time.time()
        
        # 실제 모델 연산 및 DB 검색이 일어나는 부분
        results = search_service.search(
            user_input=normalized_query,
            candidate_k=candidate_k,
            final_k=payload.top_k,
            lambda_param=payload.lambda_param,
        )
        
        # ------------------- 디버깅 로그 완료 -------------------
        elapsed_time = time.time() - step_start
        print(f"[DEBUG] 파이프라인 연산 완료! (소요 시간: {elapsed_time:.2f}초)")
        print(f"[DEBUG] 최종 추천 논문 개수: {len(results)}개")
        print(f"[DEBUG] ===========================================\n")
        # --------------------------------------------------------
        
        return {"results": results}
        
    except ValueError as exc:
        print(f"[ERROR] ValueError 발생: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        print(f"[ERROR] RuntimeError 발생: {exc}")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        print(f"[ERROR] 검색 중 알 수 없는 에러 발생: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommend")
def recommend(_: dict[str, Any]):
    raise HTTPException(status_code=501, detail="recommend endpoint is not implemented yet")