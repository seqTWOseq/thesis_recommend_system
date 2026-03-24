const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// 백엔드 서버가 없을 때 사용할 Mock 데이터
const MOCK_RESULTS = {
  results: [
    { title: "Mock Paper 1", abstract: "This is a mock abstract for testing.", score: 0.98 },
    { title: "Mock Paper 2", abstract: "Another mock abstract for UI development.", score: 0.91 },
  ],
};

export async function fetchRecommendations(query) {
  try {
    const response = await fetch(`${BASE_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) throw new Error("API error");
    return await response.json();
  } catch (error) {
    console.warn("백엔드 연결 실패 - Mock 데이터 사용:", error.message);
    return MOCK_RESULTS;
  }
}
