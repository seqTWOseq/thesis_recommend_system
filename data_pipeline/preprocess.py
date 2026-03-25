import pandas as pd
import re

def clean_text(text):
    """
    텍스트 내 불필요한 공백 및 줄바꿈을 제거하는 유틸리티 함수
    """
    if not isinstance(text, str):
        return ""
    # 줄바꿈을 띄어쓰기로 치환
    text = text.replace('\n', ' ')
    # 2개 이상의 연속된 공백을 1개로 압축 (정규표현식 사용)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_arxiv_data(input_path, output_path, categories, start_date='2019-01-01', chunk_size=5000):
    """
    대용량 ArXiv 메타데이터를 필터링하고 즉시 텍스트 전처리까지 수행하는 통합 함수
    """
    # 1. 필터링 단계 (Filtering)
    pattern = '|'.join([cat.replace('.', r'\.') for cat in categories])
    total_dropped_by_null = 0
    filtered_chunks = [] # 중간 데이터를 메모리에 보관할 리스트

    print(f"[1/2] 필터링 시작 (기준 날짜: {start_date}, 카테고리: {len(categories)}종)")

    for chunk in pd.read_json(input_path, lines=True, chunksize=chunk_size):
        # 카테고리 필터링
        filtered = chunk[chunk['categories'].str.contains(pattern, na=False)]
        
        # 결측치 제거 및 카운트
        before_dropna = len(filtered)
        filtered = filtered.dropna(subset=['title', 'abstract'])
        after_dropna = len(filtered)
        total_dropped_by_null += (before_dropna - after_dropna)
        
        # 날짜 필터링
        filtered['update_date'] = pd.to_datetime(filtered['update_date'], format='%Y-%m-%d', errors='coerce')
        filtered = filtered[filtered['update_date'] >= start_date]
        
        if not filtered.empty:
            # 필요한 컬럼만 추출 (SettingWithCopyWarning 방지를 위해 .copy() 사용)
            final_data = filtered[['id', 'title', 'abstract', 'categories', 'update_date']].copy()
            # Unix timestamp(밀리초)로 변환
            final_data['update_date'] = final_data['update_date'].astype('int64') // 10**6
            
            # 리스트에 청크 추가 (파일 저장 대신 메모리에 적재)
            filtered_chunks.append(final_data)

    if not filtered_chunks:
        print("조건에 맞는 데이터가 없습니다.")
        return None

    # 모든 청크를 하나의 데이터프레임으로 병합
    df = pd.concat(filtered_chunks, ignore_index=True)
    
    print(f"\n[1/2] 필터링 완료!")
    print(f"- 1차 수집된 데이터: {len(df)}건")
    print(f"- 결측치(Title/Abstract)로 제거된 데이터: {total_dropped_by_null}건")

    # 2. 전처리 단계 (Preprocessing)
    print("\n[2/2] 중복 제거 및 텍스트 정제 시작...")
    
    # 정렬 및 중복 제거
    sort_df = df.sort_values(by='update_date', ascending=False)
    sort_df = sort_df.drop_duplicates(subset=['id'], keep='first')
    print(f"- 중복 제거 후 남은 데이터: {len(sort_df)}건")

    # 텍스트 정제 및 page_content 생성
    sort_df['title'] = sort_df['title'].apply(clean_text)
    sort_df['abstract'] = sort_df['abstract'].apply(clean_text)
    sort_df['page_content'] = "Title: " + sort_df['title'] + ". Abstract: " + sort_df['abstract']

    # 최종 컬럼 선택 및 저장
    final_columns = ['id', 'page_content', 'update_date', 'categories']
    final_df = sort_df[final_columns]
    
    final_df.to_json(output_path, orient='records', lines=True, force_ascii=False)
    
    print(f"\n최종 처리 완료! 저장 경로: {output_path}")
    return final_df

if __name__ == "__main__":
    # 설정값 정의
    INPUT_FILE = 'data_pipeline/raw_data/arxiv-metadata-oai-snapshot.json'
    OUTPUT_FILE = 'data_pipeline/processed_data/arxiv_final.json'  # 최종 결과물만 저장
    TARGET_CATEGORIES = [
        'cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 
        'cs.NE', 'cs.RO', 'stat.ML', 'math.OC'
    ]
    START_DATE = '2019-01-01'

    # 통합 함수 실행
    final_result_df = process_arxiv_data(
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        categories=TARGET_CATEGORIES,
        start_date=START_DATE
    )
    
    if final_result_df is not None:
        print(f"\n[최종 데이터프레임 구조 확인] Shape: {final_result_df.shape}")
        print(final_result_df.head(3))