# 임베딩 - 정우
import pandas as pd
import os
import torch
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

def load_and_split_docs(file_path, nrows=10000):
    """
    JSON 데이터를 로드하고 텍스트를 청크 단위로 분할
    """
    print(f"데이터 로드 중... (최대 {nrows}행)")
    df = pd.read_json(file_path, lines=True, nrows=nrows)
    
    documents = [
        Document(page_content=row["page_content"], metadata={"id": row["id"]}) 
        for _, row in df.iterrows()
    ]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunked_docs = text_splitter.split_documents(documents)
    print(f"텍스트 분할 완료: 총 {len(chunked_docs)}개의 청크 생성")
    return chunked_docs

def get_embedding_model(model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    """
    다국어 임베딩 모델을 로드 (GPU 자동 설정)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"임베딩 모델 로드 중... (장치: {device})")
    
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device}
    )
    
def create_vector_store(model, chunked_docs):
    """
    분할된 문서들을 벡터로 변환
    """
    print("전체 조각에 대한 벡터 변환 시작 (Batch Embedding)...")
    all_texts = [doc.page_content for doc in chunked_docs]
    all_vectors = model.embed_documents(all_texts)
    
    print(f"벡터 생성 완료: {len(all_vectors)}개 (차원: {len(all_vectors[0])})")
    return np.array(all_vectors)

def search_documents(query, model, doc_vectors, chunked_docs, top_k=5):
    """
    사용자 쿼리를 기반으로 유사한 문서를 검색합니다.
    """
    # 쿼리 벡터화
    query_vector = model.embed_query(query)
    query_vector = np.array(query_vector).reshape(1, -1)
    
    # 코사인 유사도 계산
    similarities = cosine_similarity(query_vector, doc_vectors)[0]
    
    # 상위 K개 인덱스 추출
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "score": similarities[idx],
            "id": chunked_docs[idx].metadata.get("id"),
            "content": chunked_docs[idx].page_content
        })
    return results

def display_results(results, query):
    """
    검색 결과를 질문자님이 원하는 포맷으로 터미널에 출력하는 함수
    """
    print(f"\n'{query}'에 대한 검색 결과입니다:")
    
    if not results:
        print("검색 결과가 없습니다.")
        return

    for res in results:
        print("-" * 50)
        print(f"점수: {res['score']:.4f} | ID: {res['id']}")
        print(f"내용: {res['content']}")
    print("-" * 50)

def run_total_pipeline(query, file_path, nrows=10000, verbose=True):
    # 문서 로드 및 청크 분할
    docs = load_and_split_docs(file_path, nrows=nrows)

    # 모델 로드 및 벡터 생성 (GPU 활용)
    model = get_embedding_model()
    vectors = create_vector_store(model, docs)

    # 검색 실행
    results = search_documents(query, model, vectors, docs, top_k=5)
    
    if verbose:
        display_results(results, query)
    
    return vectors, results

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(BASE_DIR, 'data_pipeline', 'processed_data', 'arxiv_final.json')
    query = input("\n프로젝트 주제를 입력하세요 : ")
    vectors, results = run_total_pipeline(query, file_path)
