from contextlib import asynccontextmanager
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import chromadb
from chromadb.api.models.Collection import Collection

CURRENT_DIR = Path(__file__).resolve().parent
PERSIST_DIR = CURRENT_DIR / "vector_store"
COLLECTION_NAME = "papers"
print(f"ChromaDB 경로: {PERSIST_DIR.absolute()}")

def initialize(app: FastAPI):
    """서버 시작 시 임베딩 모델과 ChromaDB 컬렉션을 로드합니다."""
    print("임베딩 모델 로드 중...")
    app.state.encoder_model = get_embedding_model(model_name="intfloat/multilingual-e5-base")
    app.state.decoder_model = get_embedding_model(model_name="Qwen/Qwen2.5-1.5B-Instruct")
    print("ChromaDB 컬렉션 로드 중...")
    client = get_chroma_client()
    app.state.collection = client.get_collection(name=COLLECTION_NAME)
    print("초기화 완료!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize(app)
    yield


app = FastAPI(title="Semantic Article Recommender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


def get_embedding_model(model_name):
    """E5 임베딩 모델을 로드합니다."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n임베딩 모델 [{model_name}]을(를) {device} 환경에서 로드 중...")

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
    )

def get_chroma_client() -> chromadb.PersistentClient:
    """backend/vector_store 경로에 영구적인(persistent) 크로마(Chroma) 클라이언트를 생성합니다."""
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(PERSIST_DIR))