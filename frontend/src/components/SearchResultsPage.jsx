import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import SearchBar from "./SearchBar";
import ThesisResults from "./ThesisResults";
import { searchPapers } from "../api/client";

function SearchResultsPage({
  initialQuery,
  onSearch,
  prefetchedQuery = "",
  prefetchedResults = null,
}) {
  const [results, setResults] = useState([]);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [listError, setListError] = useState(null);
  const [currentQuery, setCurrentQuery] = useState(initialQuery || "");

  useEffect(() => {
    setCurrentQuery(initialQuery || "");
  }, [initialQuery]);

  useEffect(() => {
    const next = (initialQuery || "").trim();
    if (!next) {
      setResults([]);
      setListError(null);
      setFetchLoading(false);
      return;
    }

    if (prefetchedQuery === next && Array.isArray(prefetchedResults)) {
      setResults(prefetchedResults);
      setListError(null);
      setFetchLoading(false);
      return;
    }

    let mounted = true;
    const run = async () => {
      setFetchLoading(true);
      setListError(null);
      try {
        const data = await searchPapers(next, 100);
        if (!mounted) return;
        if (!data.ok) {
          setListError(data.userMessage);
          setResults([]);
        } else {
          setResults(data.results || []);
        }
      } finally {
        if (mounted) {
          setFetchLoading(false);
        }
      }
    };

    run();
    return () => {
      mounted = false;
    };
  }, [initialQuery]);

  const handleSearch = async (query) => {
    setCurrentQuery(query);
    setListError(null);
    setSubmitLoading(true);
    try {
      const res = await onSearch?.(query);
      if (res && !res.ok && res.userMessage) {
        setListError(res.userMessage);
        setResults([]);
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const barLoading = fetchLoading || submitLoading;

  return (
    <main className="min-h-screen bg-[#DBD3C7] px-4 py-8">
      <section className="w-full max-w-5xl mx-auto">
        <div className="w-full">
          <SearchBar
            onSearch={handleSearch}
            initialQuery={currentQuery}
            fullWidth
            loading={barLoading}
            apiError={listError}
            onDismissApiError={() => setListError(null)}
          />
        </div>

        <div className="w-full mt-6 rounded-2xl border border-[#8DA399] bg-white/70 p-4 sm:p-6 shadow-sm">
          <p className="text-sm sm:text-base text-[#374151]/80 mb-4">
            검색어:{" "}
            <span className="font-semibold text-[#374151]">
              {currentQuery || "-"}
            </span>
          </p>

          {barLoading ? (
            <div
              className="flex flex-col items-center justify-center gap-2 py-12 text-[#374151]"
              aria-live="polite"
            >
              <Loader2
                className="animate-spin text-[#8DA399]"
                size={36}
                strokeWidth={2}
                aria-hidden
              />
              <span className="text-sm opacity-80">Loading results…</span>
            </div>
          ) : (
            <ThesisResults results={results} />
          )}
        </div>
      </section>
    </main>
  );
}

export default SearchResultsPage;
