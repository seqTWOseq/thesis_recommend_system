import os
from pathlib import Path
import torch

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERSIST_DIR = Path(os.path.join(BASE_DIR, "backend", "vector_store"))
COLLECTION_NAME = "papers"

def init_search_system():
    """데이터베이스와 임베딩 모델을 메모리에 로드하여 검색 준비를 마칩니다."""
    print("시스템 초기화 중... (데이터베이스 및 AI 모델 로드)")
    
    # DB 연결
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embedding_model = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        model_kwargs={"device": device}
    )
    
    print(f"초기화 완료! (총 {collection.count()}개의 논문이 검색 대기 중입니다.)\n")
    return collection, embedding_model

def search_papers(query_text: str, collection, embedding_model, top_k: int = 3):
    """사용자의 쿼리와 유사한 논문을 ChromaDB에서 찾아 반환합니다."""
    
    # E5 모델 권장 사항에 따라 검색어에 접두사 추가
    formatted_query = f"query: {query_text}"
    
    # 검색어를 벡터(숫자 배열)로 변환
    query_vector = embedding_model.embed_query(formatted_query)
    
    # ChromaDB를 통해 가장 유사도 거리가 가까운 논문 검색
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    return results

if __name__ == "__main__":
    # 시스템 초기화 (1회만 실행)
    db_collection, model = init_search_system()
    
    # 대화형 검색 루프 시작
    print("=" * 60)
    print("AI 논문 검색 시스템에 오신 것을 환영합니다.")
    print("   (종료하시려면 'q', 'quit', 'exit' 중 하나를 입력하세요)")
    print("=" * 60)
    
    while True:
        # 사용자로부터 input 받기 (예: "강화학습을 이용한 추천 시스템", "Attention is All You Need")
        user_input = input("\n프로젝트 주제를 입력하세요: ").strip()
        
        # 종료 조건 처리
        if user_input.lower() in ['q', 'quit', 'exit']:
            print("검색 시스템을 종료합니다. 감사합니다!")
            break
            
        if not user_input:
            print("검색어를 입력해주세요.")
            continue
            
        print("\n유사한 논문을 찾는 중...")
        
        # 검색 실행 (상위 3개 추출)
        search_results = search_papers(user_input, db_collection, model, top_k=5)
        
        # 결과가 없는 경우 예외 처리
        if not search_results['ids'][0]:
            print("일치하는 검색 결과가 없습니다.")
            continue
            
        # 검색 결과 깔끔하게 출력하기
        print(f"\n'{user_input}'에 대한 상위 검색 결과:")
        for i in range(len(search_results['ids'][0])):
            doc_id = search_results['ids'][0][i]
            document = search_results['documents'][0][i]
            distance = search_results['distances'][0][i]
            metadata = search_results['metadatas'][0][i]
            
            print("-" * 60)
            print(f"[{i+1}위] | 논문 ID: {doc_id}")
            print(f"유사도: {1.0 - distance:.4f}")
            if metadata and 'categories' in metadata:
                print(f"카테고리: {metadata['categories']}")
            
            # 본문 내용이 너무 길 수 있으므로 300자까지만 자르기 및 접두사 정리
            clean_document = document.replace("passage: ", "", 1)
            print(f"\n논문 내용 :\n{clean_document}")