import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const apiClient = axios.create({
  baseURL: BASE_URL,
  // HyDE/임베딩/MMR 파이프라인이 한 번 요청에 오래 걸릴 수 있어
  // 로컬 환경에서 불필요한 timeout("Network error")을 줄입니다.
  timeout: 30000,
});

export async function fetchRecommendations(query) {
  return searchPapers(query, 5);
}

export async function searchPapers(query, topK = 100) {
  try {
    const response = await apiClient.post("/api/search", { query, top_k: topK });
    const results = response?.data?.results || [];
    return { ok: true, results };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (
        error.code === "ERR_NETWORK" ||
        error.code === "ECONNABORTED" ||
        !error.response
      ) {
        return {
          ok: false,
          userMessage: "Network error. Please check your connection.",
        };
      }
      return {
        ok: false,
        userMessage: "Search failed. Please try again.",
      };
    }
    return {
      ok: false,
      userMessage: "Search failed. Please try again.",
    };
  }
}
