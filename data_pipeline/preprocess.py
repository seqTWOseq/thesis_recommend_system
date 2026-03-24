import pandas as pd
import os

RAW_DATA_DIR = "raw_data"
PROCESSED_DATA_DIR = "processed_data"

def preprocess():
    # raw_data 폴더의 CSV 파일 읽기
    raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]
    if not raw_files:
        print("raw_data/ 폴더에 CSV 파일이 없습니다.")
        return

    for filename in raw_files:
        path = os.path.join(RAW_DATA_DIR, filename)
        df = pd.read_csv(path)

        # 결측치 제거
        df = df.dropna()

        # 중복 제거
        df = df.drop_duplicates()

        # 정제된 파일 저장
        output_path = os.path.join(PROCESSED_DATA_DIR, f"processed_{filename}")
        df.to_csv(output_path, index=False)
        print(f"저장 완료: {output_path} ({len(df)}행)")

if __name__ == "__main__":
    preprocess()
