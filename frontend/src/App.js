import React, { useState } from "react";
import SearchBar from "./components/SearchBar";
import ArticleList from "./components/ArticleList";
import { fetchRecommendations } from "./api/client";

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query) => {
    setLoading(true);
    const data = await fetchRecommendations(query);
    setResults(data.results || []);
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}>
      <h1>논문 추천 시스템</h1>
      <SearchBar onSearch={handleSearch} />
      {loading ? <p>검색 중...</p> : <ArticleList articles={results} />}
    </div>
  );
}

export default App;
