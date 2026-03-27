import React, { useEffect, useState } from "react";
import SearchBar from "./SearchBar";
import ArticleList from "./ArticleList";
import { searchPapers } from "../api/client";

function SearchResultsPage({ initialQuery, onSearch, prefetchedQuery = "", prefetchedResults = null }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(initialQuery || "");

  useEffect(() => {
    setCurrentQuery(initialQuery || "");
  }, [initialQuery]);

  useEffect(() => {
    const next = (initialQuery || "").trim();
    if (!next) {
      setResults([]);
      return;
    }

    if (prefetchedQuery === next && Array.isArray(prefetchedResults)) {
      setResults(prefetchedResults);
      setLoading(false);
      return;
    }

    let mounted = true;
    const run = async () => {
      setLoading(true);
      try {
        const data = await searchPapers(next, 100);
        if (mounted) {
          setResults(data.results || []);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    run();
    return () => {
      mounted = false;
    };
  }, [initialQuery]);

  const handleSearch = (query) => {
    setCurrentQuery(query);
    onSearch?.(query);
  };

  return (
    <main className="min-h-screen bg-[#F9F9F7] px-4 py-8">
      <section className="w-full max-w-5xl mx-auto">
        <div className="w-full">
          <SearchBar
            onSearch={handleSearch}
            initialQuery={currentQuery}
            fullWidth
          />
        </div>

        <div className="w-full mt-6 rounded-2xl border border-[#8DA399] bg-white/70 p-4 sm:p-6 shadow-sm">
          <p className="text-sm sm:text-base text-[#374151]/80 mb-4">
            검색어: <span className="font-semibold text-[#374151]">{currentQuery || "-"}</span>
          </p>

          {loading ? (
            <p className="text-[#374151] text-sm sm:text-base text-center opacity-70">
              검색 중...
            </p>
          ) : (
            <ArticleList articles={results} />
          )}
        </div>
      </section>
    </main>
  );
}

export default SearchResultsPage;
