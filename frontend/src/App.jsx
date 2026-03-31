import React, { useCallback, useEffect, useMemo, useState } from "react";
import MainLayout from "./components/MainLayout";
import SearchResultsPage from "./components/SearchResultsPage";
import { searchPapers } from "./api/client";
import thesisImageUrl from "../img/Thesis.jpg";

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [searchText, setSearchText] = useState(window.location.search);
  const [routeState, setRouteState] = useState(window.history.state || {});
  const [homeLoading, setHomeLoading] = useState(false);
  const [homeSearchError, setHomeSearchError] = useState(null);

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
    if (!next) return { ok: false };

    const shouldShowHomeLoading = path !== "/search";
    if (shouldShowHomeLoading) {
      setHomeSearchError(null);
      setHomeLoading(true);
    }

    try {
      const data = await searchPapers(next, 100);
      if (!data.ok) {
        if (shouldShowHomeLoading) {
          setHomeSearchError(data.userMessage);
        }
        return { ok: false, userMessage: data.userMessage };
      }

      const nextState = {
        prefetchedQuery: next,
        prefetchedResults: data.results || [],
      };
      const nextUrl = `/search?q=${encodeURIComponent(next)}`;
      window.history.pushState(nextState, "", nextUrl);
      setRouteState(nextState);
      setPath("/search");
      setSearchText(window.location.search);
      return { ok: true };
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

  const handleLogoClick = useCallback(() => {
    if (path === "/search") {
      window.history.pushState({}, "", "/");
      setPath("/");
      setSearchText("");
      setRouteState({});
    } else {
      window.location.reload();
    }
  }, [path]);

  if (path === "/search") {
    return (
      <SearchResultsPage
        initialQuery={queryFromUrl}
        onSearch={handleSearchNavigation}
        onLogoClick={handleLogoClick}
        prefetchedQuery={routeState?.prefetchedQuery || ""}
        prefetchedResults={routeState?.prefetchedResults}
      />
    );
  }

  return (
    <MainLayout
      onSearch={handleSearchNavigation}
      onLogoClick={handleLogoClick}
      // backgroundImageUrl={thesisImageUrl}
      searchLoading={homeLoading}
      searchError={homeSearchError}
      onDismissSearchError={() => setHomeSearchError(null)}
    />
  );
}

