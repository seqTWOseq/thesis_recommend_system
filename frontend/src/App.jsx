import React, { useState } from "react";
import MainLayout from "./components/MainLayout";
import ArticleList from "./components/ArticleList";
import { fetchRecommendations } from "./api/client";
import testImageUrl from "../img/test.png";

export default function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query) => {
    setLoading(true);
    try {
      const data = await fetchRecommendations(query);
      setResults(data.results || []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout onSearch={handleSearch} backgroundImageUrl={testImageUrl}>
      <div className="w-full max-w-3xl">
        {loading ? (
          <p className="text-[#374151] text-sm sm:text-base mt-3 text-center opacity-70">
            검색 중...
          </p>
        ) : results?.length ? (
          <div className="mt-4 max-h-[24vh] overflow-auto pr-1">
            <ArticleList articles={results} />
          </div>
        ) : null}
      </div>
    </MainLayout>
  );
}

