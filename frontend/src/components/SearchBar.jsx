import React, { useId, useState } from "react";
import { Search } from "lucide-react";

function SearchBar({ onSearch }) {
  const id = useId();
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const next = query.trim();
    if (!next) return;
    onSearch?.(next);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full flex justify-center">
      <div className="w-full max-w-3xl rounded-full bg-[#FFFFFF] shadow-sm px-2 py-2 flex items-center gap-2 focus-within:ring-2 focus-within:ring-[#8DA399]/30 focus-within:ring-offset-2 focus-within:ring-offset-white transition-shadow">
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
          aria-label="검색"
          className="w-11 h-11 rounded-full bg-[#8DA399] text-white flex items-center justify-center transition-transform transition-colors duration-200 hover:bg-[#7F968C] hover:scale-[1.05] focus:outline-none focus:ring-2 focus:ring-[#8DA399]/30"
        >
          <Search size={20} strokeWidth={2.25} />
        </button>
      </div>
    </form>
  );
}

export default SearchBar;
