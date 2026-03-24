from fastapi import APIRouter
from pydantic import BaseModel
from core.vector_db import search_similar

router = APIRouter()

class RecommendRequest(BaseModel):
    query: str

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/recommend")
def recommend(request: RecommendRequest):
    results = search_similar(request.query)
    return {"results": results}
