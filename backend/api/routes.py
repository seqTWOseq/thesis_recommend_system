from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RecommendRequest(BaseModel):
    query: str


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/recommend")
def recommend(request: RecommendRequest):
    # TODO: search_similar 구현 후 연결
    return {"results": []}
