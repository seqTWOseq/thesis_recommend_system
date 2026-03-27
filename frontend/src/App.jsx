import React, { useEffect, useMemo, useState } from "react";
import MainLayout from "./components/MainLayout";
import SearchResultsPage from "./components/SearchResultsPage";
import { searchPapers } from "./api/client";
import testImageUrl from "../img/test.png";

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [searchText, setSearchText] = useState(window.location.search);
  const [routeState, setRouteState] = useState(window.history.state || {});
  const [homeLoading, setHomeLoading] = useState(false);

  useEffect(() => {
    const onPopState = (event) => {
      setPath(window.location.pathname);
      setSearchText(window.location.search);
      setRouteState(event.state || {});
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const handleSearchNavigation = async (query) => {
    const next = query.trim();
    if (!next) return;

    const shouldShowHomeLoading = path !== "/search";
    if (shouldShowHomeLoading) {
      setHomeLoading(true);
    }

    try {
      const data = await searchPapers(next, 100);
      const nextResults = data?.results || [];
      const nextState = {
        prefetchedQuery: next,
        prefetchedResults: nextResults,
      };
      const nextUrl = `/search?q=${encodeURIComponent(next)}`;
      window.history.pushState(nextState, "", nextUrl);
      setRouteState(nextState);
      setPath("/search");
      setSearchText(window.location.search);
    } finally {
      if (shouldShowHomeLoading) {
        setHomeLoading(false);
      }
    }
  };

  const queryFromUrl = useMemo(() => {
    const params = new URLSearchParams(searchText);
    return params.get("q") || "";
  }, [searchText]);

  if (path === "/search") {
    return (
      <SearchResultsPage
        initialQuery={queryFromUrl}
        onSearch={handleSearchNavigation}
        prefetchedQuery={routeState?.prefetchedQuery || ""}
        prefetchedResults={routeState?.prefetchedResults}
      />
    );
  }

  return (
    <MainLayout
      onSearch={handleSearchNavigation}
      backgroundImageUrl={testImageUrl}
      searchLoading={homeLoading}
    />
  );
}

