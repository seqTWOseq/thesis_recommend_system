import React, { useState } from "react";

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="논문 주제를 입력하세요..."
        style={{ flex: 1, padding: "0.5rem", fontSize: "1rem" }}
      />
      <button type="submit" style={{ padding: "0.5rem 1rem" }}>
        검색
      </button>
    </form>
  );
}

export default SearchBar;
