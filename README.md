# Semantic Article Recommender

논문 추천 시스템 - 모노레포 구조

## 프로젝트 구조

```
thesis_recommend_system/
├── data_pipeline/    # 데이터 전처리 (담당: B)
├── backend/          # FastAPI 서버 + AI/DB 로직 (담당: C, D, E)
└── frontend/         # React UI (담당: F)
```

## 실행 방법

### 1. 데이터 전처리
```bash
cd data_pipeline
python preprocess.py
```

### 2. 백엔드 서버 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## API 명세

| Method | Endpoint     | 설명              |
|--------|--------------|-------------------|
| GET    | /health      | 서버 상태 확인    |
| POST   | /recommend   | 논문 추천 요청    |

### POST /recommend

**Request Body**
```json
{
  "query": "검색할 논문 주제 텍스트"
}
```

**Response**
```json
{
  "results": [
    {
      "title": "논문 제목",
      "abstract": "초록",
      "score": 0.95
    }
  ]
}
```
