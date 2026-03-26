from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class RecommendRequest(BaseModel):
    query: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

# 실제 ChromaDB 데이터 기반 Mock 데이터
MOCK_RESULTS = [
    {
        "title": "Cubic Discrete Diffusion: Discrete Visual Generation on High-Dimensional Representation Tokens",
        "url": "https://arxiv.org/abs/2603.19232",
        "score": 0.97,
        "snippet": "Visual generation with discrete tokens has gained significant attention as it enables a unified token prediction paradigm shared with language models, promising seamless multimodal architecture."
    },
    {
        "title": "Nemotron-Cascade 2: Post-Training LLMs with Cascade RL and Multi-Domain On-Policy Distillation",
        "url": "https://arxiv.org/abs/2603.19220",
        "score": 0.93,
        "snippet": "We introduce Nemotron-Cascade 2, an open 30B MoE model with 3B activated parameters that delivers best-in-class reasoning and strong agentic capabilities."
    },
    {
        "title": "DriveTok: 3D Driving Scene Tokenization for Unified Multi-View Reconstruction and Understanding",
        "url": "https://arxiv.org/abs/2603.19219",
        "score": 0.89,
        "snippet": "With the growing adoption of vision-language-action models and world models in autonomous driving systems, scalable image tokenization becomes crucial as the interface for the visual mod."
    },
]

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/api/search")
def search(request: SearchRequest):
    # Mock: 실제 검색 없이 고정 데이터 반환 (top_k 적용)
    return {"results": MOCK_RESULTS[:request.top_k]}

@router.post("/recommend")
def recommend(request: RecommendRequest):
    # TODO: search_similar 구현 후 연결
    return {"results": []}
