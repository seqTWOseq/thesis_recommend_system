from core.embedding import get_embeddings
import faiss
import numpy as np

# 전역 인덱스 및 문서 저장소
_index = None
_documents = []

def build_index(texts: list[str], metadatas: list[dict]):
    global _index, _documents
    embeddings = get_embeddings()
    vectors = np.array(embeddings.embed_documents(texts), dtype="float32")

    dim = vectors.shape[1]
    _index = faiss.IndexFlatIP(dim)  # 코사인 유사도 (내적)
    faiss.normalize_L2(vectors)
    _index.add(vectors)
    _documents = metadatas
    print(f"인덱스 구축 완료: {len(texts)}개 문서")

def search_similar(query: str, top_k: int = 5) -> list[dict]:
    if _index is None:
        return []
    embeddings = get_embeddings()
    query_vec = np.array([embeddings.embed_query(query)], dtype="float32")
    faiss.normalize_L2(query_vec)
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(_documents):
            result = dict(_documents[idx])
            result["score"] = round(float(score), 4)
            results.append(result)
    return results