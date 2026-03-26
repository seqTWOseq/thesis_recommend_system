import os

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity


def load_docs(file_path, nrows: int | None = None):
    """JSONL 파일을 청킹(chunking) 없이 로드하고 E5 passage 접두사를 추가합니다."""
    print("데이터 로듭 중...")
    
    # nrows가 None이면 전체 데이터를 읽습니다.
    if nrows is None:
        print(f"데이터 로드 중... (전체 데이터)")
        df = pd.read_json(file_path, lines=True)
    else:
        print(f"데이터 로드 중... (최대 {nrows}행)")
        df = pd.read_json(file_path, lines=True, nrows=nrows)

    documents = []
    for _, row in df.iterrows():
        content = f"passage: {row['page_content']}"
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "id": row["id"],
                    "update_date": row.get("update_date"),
                    "categories": row.get("categories"),
                },
            )
        )

    print(f"총 {len(documents)}개의 문서를 로드했습니다.")
    return documents


def get_embedding_model(model_name="intfloat/multilingual-e5-base"):
    """E5 임베딩 모델을 로드합니다."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n임베딩 모델 [{model_name}]을(를) {device} 환경에서 로드 중...")

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
    )


def create_vector_store(model, documents, batch_size=10000):
    """각 문서를 배치 단위로 나누어 벡터로 임베딩하고 tqdm으로 진행 상황을 확인합니다."""
    
    print(f"문서 임베딩 생성 중... (총 {len(documents)}개, 배치 크기: {batch_size})")
    all_texts = [doc.page_content for doc in documents]
    all_vectors = []

    # 전체 데이터를 batch_size만큼씩 잘라서 임베딩 처리
    for i in tqdm(range(0, len(all_texts), batch_size), desc="임베딩 진행률", unit="배치"):
        batch_texts = all_texts[i : i + batch_size]
        batch_vectors = model.embed_documents(batch_texts)
        all_vectors.extend(batch_vectors)

    print(f"\n{len(all_vectors)}개의 벡터를 생성했습니다. (차원: {len(all_vectors[0])})")
    return np.array(all_vectors)


def prepare_vectordb_data(documents, all_vectors):
    """하나의 문서가 하나의 벡터에 매핑되는 DataFrame을 빌드합니다."""
    print("\n벡터 DB용 DataFrame 준비 중...")
    ready_data = []

    for i, doc in enumerate(documents):
        ready_data.append(
            {
                "id": str(doc.metadata.get("id")),
                "update_date": doc.metadata.get("update_date"),
                "categories": doc.metadata.get("categories"),
                "page_content": doc.page_content,
                "vector": all_vectors[i].tolist(),
            }
        )

    df_ready_for_db = pd.DataFrame(ready_data)
    print(f"총 {len(df_ready_for_db)}행의 DataFrame이 생성되었습니다.")
    return df_ready_for_db


def prepare_embedding_artifacts(file_path, nrows: int | None = None):
    """검색 및 DB 저장 모두에 사용되는 공통 아티팩트를 생성합니다."""
    docs = load_docs(file_path, nrows=nrows)
    model = get_embedding_model()
    vectors = create_vector_store(model, docs)
    df_vector_db = prepare_vectordb_data(docs, vectors)
    return docs, model, vectors, df_vector_db


def build_vector_db_dataframe(file_path, nrows: int | None = None):
    """벡터 DB 저장에 필요한 DataFrame만 빌드합니다."""
    _, _, _, df_vector_db = prepare_embedding_artifacts(file_path, nrows=nrows)
    return df_vector_db


def search_documents(query, model, doc_vectors, df_vector_db, top_k=5):
    """E5 쿼리 접두사를 사용하여 가장 유사한 문서를 검색합니다."""
    formatted_query = f"query: {query}"
    query_vector = model.embed_query(formatted_query)
    query_vector = np.array(query_vector).reshape(1, -1)

    similarities = cosine_similarity(query_vector, doc_vectors)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        matched_row = df_vector_db.iloc[idx]
        results.append(
            {
                "score": similarities[idx],
                "id": matched_row["id"],
                "content": matched_row["page_content"],
            }
        )
    return results


def display_results(results, query):
    """검색 결과를 출력합니다."""
    print(f"\n'{query}'에 대한 검색 결과:")
    if not results:
        print("결과를 찾을 수 없습니다.")
        return

    for i, res in enumerate(results, 1):
        print("=" * 70)
        print(f"[{i}] 유사도 점수: {res['score']:.4f} | 문서 ID: {res['id']}")
        print("-" * 70)
        print(res["content"].replace("passage: ", "", 1))
    print("=" * 70)


def run_total_pipeline(query, file_path, nrows: int | None = 100000, verbose=True):
    """전체 파이프라인을 실행합니다."""
    docs, model, vectors, df_vector_db = prepare_embedding_artifacts(
        file_path,
        nrows=nrows,
    )
    results = search_documents(query, model, vectors, df_vector_db, top_k=5)

    if verbose:
        display_results(results, query)

    return df_vector_db, vectors, results


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, "backend", "vector_store", "arxiv_final.json")

    query = input("\n프로젝트 주제를 입력하세요: ")
    # 테스트를 위해 N개만 로드하도록 설정 (실제 사용 시 nrows=None으로 변경)
    df_vector_db, vectors, results = run_total_pipeline(query, file_path, nrows=10000)

    print("\n[참조] DataFrame 미리보기:")
    print(df_vector_db.head(5))
