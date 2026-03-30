from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from core.DB_test import run_search_pipeline
except ModuleNotFoundError:
    try:
        from backend.core.DB_test import run_search_pipeline
    except ModuleNotFoundError:
        from DB_test import run_search_pipeline  # type: ignore


router = APIRouter()


class RecommendRequest(BaseModel):
    query: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 100


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/api/search")
def search(request: SearchRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        results = run_search_pipeline(
            user_input=request.query,
            candidate_k=request.top_k,
            final_k=request.top_k,
        )
        return {"results": results}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommend")
def recommend(request: RecommendRequest):
    # TODO: connect recommendation endpoint when the next stage is ready.
    return {"results": []}
