import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
});

// 백엔드 서버가 없을 때 사용할 Mock 데이터
const MOCK_RESULTS = {
  results: [
    {
      title:
        "Cubic Discrete Diffusion: Discrete Visual Generation on High-Dimensional Representation Tokens",
      snippet:
        "Visual generation with discrete tokens enables unified multimodal token prediction shared with language models.",
      score: 0.97,
      url: "https://arxiv.org/abs/2603.19232",
    },
    {
      title:
        "Nemotron-Cascade 2: Post-Training LLMs with Cascade RL and Multi-Domain On-Policy Distillation",
      snippet:
        "An open 30B MoE model delivering strong reasoning and agentic capabilities through cascade reinforcement learning.",
      score: 0.93,
      url: "https://arxiv.org/abs/2603.19220",
    },
    {
      title:
        "DriveTok: 3D Driving Scene Tokenization for Unified Multi-View Reconstruction and Understanding",
      snippet:
        "Scalable image tokenization for autonomous driving supports unified reconstruction and scene understanding.",
      score: 0.89,
      url: "https://arxiv.org/abs/2603.19219",
    },
    {
      title: "Efficient Retriever Tuning for Domain-Specific QA Systems",
      snippet:
        "Retriever fine-tuning improves recall and end-to-end answer quality in specialized question answering workflows.",
      score: 0.87,
      url: "https://arxiv.org/abs/2401.01234",
    },
    {
      title: "Long-Context Ranking with Hybrid Sparse and Dense Signals",
      snippet:
        "Hybrid ranking combines lexical and semantic signals to improve relevance on long-context technical documents.",
      score: 0.84,
      url: "https://arxiv.org/abs/2402.05678",
    },
  ],
};

export async function fetchRecommendations(query) {
  return searchPapers(query, 5);
}

export async function searchPapers(query, topK = 100) {
  try {
    const response = await apiClient.post("/api/search", { query, top_k: topK });
    const results = response?.data?.results || [];
    return { results: results.length ? results : MOCK_RESULTS.results };
  } catch (error) {
    console.warn("백엔드 연결 실패 - Mock 데이터 사용:", error.message);
    return MOCK_RESULTS;
  }
}
