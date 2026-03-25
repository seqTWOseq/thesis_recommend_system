import pandas as pd
import os
import torch
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

def load_docs(file_path, nrows=10000):
    """
    JSON 데이터를 로드합니다. (청크 분할 없음!)
    """
    print(f"데이터 로드 중... (최대 {nrows}행)")
    df = pd.read_json(file_path, lines=True, nrows=nrows)
    
    documents = []
    for _, row in df.iterrows():
        # E5 모델의 규칙에 따라 문서 앞에는 'passage: '를 붙여줍니다.
        content = f"passage: {row['page_content']}"
        
        documents.append(
            Document(
                page_content=content, 
                metadata={
                    "id": row["id"],
                    "update_date": row.get("update_date", None)
                }
            )
        )
        
    print(f"데이터 로드 완료: 총 {len(documents)}개의 전체 문서 대기 중")
    return documents

def get_embedding_model(model_name="intfloat/multilingual-e5-base"):
    """
    E5 다국어 임베딩 모델을 로드합니다. (512 토큰 지원, 768 차원)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n임베딩 모델 로드 중... [{model_name}] (장치: {device})")
    
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device}
    )
    
def create_vector_store(model, documents):
    """
    문서 전체를 자르지 않고 통째로 벡터 변환
    """
    print("전체 문서에 대한 벡터 변환 시작...")
    all_texts = [doc.page_content for doc in documents]
    all_vectors = model.embed_documents(all_texts)
    
    print(f"벡터 생성 완료: {len(all_vectors)}개 (차원: {len(all_vectors[0])})")
    return np.array(all_vectors)

def prepare_vectordb_data(documents, all_vectors):
    """
    1문서 = 1벡터 구조의 깔끔한 DataFrame 생성
    """
    print("\n벡터 DB 적재용 데이터프레임 생성 중...")
    ready_data = []
    
    for i, doc in enumerate(documents):
        ready_data.append({
            "id": str(doc.metadata.get("id")),         # 원본 ID가 곧 고유 ID (청크가 없으므로)
            "update_date": doc.metadata.get("update_date"),
            "page_content": doc.page_content,          # 제목+초록 전체
            "vector": all_vectors[i].tolist()          # 768차원 임베딩 벡터
        })
        
    df_ready_for_db = pd.DataFrame(ready_data)
    print(f"DataFrame 생성 완료: 총 {len(df_ready_for_db)}행")
    
    return df_ready_for_db

def search_documents(query, model, doc_vectors, df_vector_db, top_k=5):
    """
    E5 모델 규칙에 맞게 쿼리를 변환하여 유사도 검색을 수행합니다.
    """
    # E5 모델 규칙: 검색어 앞에는 'query: '를 붙입니다.
    formatted_query = f"query: {query}"
    
    query_vector = model.embed_query(formatted_query)
    query_vector = np.array(query_vector).reshape(1, -1)
    
    # 코사인 유사도 계산
    similarities = cosine_similarity(query_vector, doc_vectors)[0]
    
    # 상위 K개 추출
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        matched_row = df_vector_db.iloc[idx]
        results.append({
            "score": similarities[idx],
            "id": matched_row["id"],
            "content": matched_row["page_content"]
        })
    return results

def display_results(results, query):
    print(f"\n'{query}'에 대한 검색 결과 :")
    if not results:
        print("검색 결과가 없습니다.")
        return
        
    for i, res in enumerate(results, 1):
        print("=" * 70)
        print(f"[{i}순위] 점수: {res['score']:.4f} | 문서 ID: {res['id']}")
        print("-" * 70)
        content = res['content'].replace("passage: ", "") # 출력할 때는 Prefix 제거
        print(content)
    print("=" * 70)

def run_total_pipeline(query, file_path, nrows=100000, verbose=True):
    # 문서 로드 (분할 없음)
    docs = load_docs(file_path, nrows=nrows)

    # E5 모델 로드 및 벡터 생성 (768차원)
    model = get_embedding_model()
    vectors = create_vector_store(model, docs)

    # DataFrame 생성 (1문서 = 1벡터)
    df_vector_db = prepare_vectordb_data(docs, vectors)
    
    # 전체 문맥 기반 Top-K 검색
    results = search_documents(query, model, vectors, df_vector_db, top_k=5)

    if verbose:
        display_results(results, query)
    
    return df_vector_db, vectors, results

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(BASE_DIR, 'data_pipeline', 'processed_data', 'arxiv_final.json')

    query = input("\n프로젝트 주제를 입력하세요 : ")
    
    # 파이프라인 실행하여 DataFrame 반환받기
    df_vector_db, vectors, results = run_total_pipeline(query, file_path, nrows=10000)
    
    # 결과 확인 (테스트 출력)
    print("\n[참고] 완성된 DataFrame 구조:")
    print(df_vector_db.head(5))