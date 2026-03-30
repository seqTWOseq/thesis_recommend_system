from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

try:
    from core.DB_test import SearchService, build_runtime_resources
except ModuleNotFoundError:
    try:
        from backend.core.DB_test import SearchService, build_runtime_resources
    except ModuleNotFoundError:
        from DB_test import SearchService, build_runtime_resources  # type: ignore


def initialize(app: FastAPI) -> None:
    """서버 시작 시 검색 리소스와 서비스를 1회 초기화합니다."""
    print("검색 리소스 초기화 중...")
    resources = build_runtime_resources()
    app.state.search_service = SearchService(resources)
    print("검색 리소스 초기화 완료!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize(app)
    yield


app = FastAPI(
    title="Semantic Article Recommender API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Dev 환경에서 프론트 주소가 `localhost`/`127.0.0.1`/포트에 따라 달라질 수 있어
    # 브라우저 CORS 차단으로 인한 "Network error"를 줄이기 위해 허용 범위를 확장합니다.
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)