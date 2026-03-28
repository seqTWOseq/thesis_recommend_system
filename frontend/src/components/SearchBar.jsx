import React, { useEffect, useId, useState } from "react";
import { Search } from "lucide-react";

function SearchBar({
  onSearch,
  initialQuery = "",
  fullWidth = false,
  loading = false,
}) {
  const id = useId();
  const [query, setQuery] = useState("");

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (loading) return;
    const next = query.trim();
    if (!next) return;
    onSearch?.(next);
  };

  const innerBarClass =
    `w-full ${fullWidth ? "" : "max-w-3xl"} rounded-full bg-[#FFFFFF] shadow-sm px-2 py-2 flex items-center gap-2 transition-shadow ` +
    (loading
      ? "focus-within:ring-0"
      : "focus-within:ring-2 focus-within:ring-[#8DA399]/30 focus-within:ring-offset-2 focus-within:ring-offset-white");

  const fields = (
    <>
      <label htmlFor={id} className="sr-only">
        논문 검색
      </label>
      <input
        id={id}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="찾으시는 논문의 제목이나 키워드를 입력하세요..."
        className="flex-1 bg-transparent text-[#374151] placeholder:text-[#8DA399] outline-none rounded-full px-4 py-2 text-base sm:text-lg"
      />
      <button
        type="submit"
        aria-label={loading ? "검색 중" : "검색"}
        disabled={loading}
        className="w-11 h-11 rounded-full bg-[#8DA399] text-white flex items-center justify-center transition-transform transition-colors duration-200 hover:bg-[#7F968C] hover:scale-[1.05] focus:outline-none focus:ring-2 focus:ring-[#8DA399]/30 disabled:opacity-70 disabled:pointer-events-none"
      >
        <Search size={20} strokeWidth={2.25} />
      </button>
    </>
  );

  return (
    <form onSubmit={handleSubmit} className="w-full flex justify-center">
      {loading ? (
        <div className={`search-bar-rainbow-ring w-full ${fullWidth ? "" : "max-w-3xl"} shadow-sm rounded-full`}>
          <div className={innerBarClass}>{fields}</div>
        </div>
      ) : (
        <div className={innerBarClass}>{fields}</div>
      )}
    </form>
  );
}

export default SearchBar;