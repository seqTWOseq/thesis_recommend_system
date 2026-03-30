import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
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
