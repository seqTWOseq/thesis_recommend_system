from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


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

    try:
        results = search_service.search(
            user_input=normalized_query,
            candidate_k=candidate_k,
            final_k=payload.top_k,
            lambda_param=payload.lambda_param,
        )
        return {"results": results}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommend")
def recommend(_: dict[str, Any]):
    raise HTTPException(status_code=501, detail="recommend endpoint is not implemented yet")