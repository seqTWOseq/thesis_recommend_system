import React, { useEffect, useId, useState } from "react";
import { Loader2, Search } from "lucide-react";
import { validateSearchInput } from "../utils/searchValidation";

function SearchBar({
  onSearch,
  initialQuery = "",
  fullWidth = false,
  loading = false,
  apiError = null,
  onDismissApiError,
}) {
  const id = useId();
  const [query, setQuery] = useState("");
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const displayError = validationError || apiError;

  const handleChange = (e) => {
    setValidationError("");
    onDismissApiError?.();
    setQuery(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    const validation = validateSearchInput(query);
    if (!validation.ok) {
      setValidationError(validation.message);
      return;
    }

    setValidationError("");
    onDismissApiError?.();
    await onSearch?.(validation.queryForApi);
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
        onChange={handleChange}
        placeholder="찾으시는 논문의 제목이나 키워드를 입력하세요..."
        className="flex-1 bg-transparent text-[#374151] placeholder:text-[#8DA399] outline-none rounded-full px-4 py-2 text-base sm:text-lg"
        aria-invalid={displayError ? "true" : "false"}
        aria-describedby={displayError ? `${id}-error` : undefined}
      />
      <button
        type="submit"
        aria-label={loading ? "검색 중" : "검색"}
        disabled={loading}
        className="w-11 h-11 rounded-full bg-[#8DA399] text-white flex items-center justify-center transition-transform transition-colors duration-200 hover:bg-[#7F968C] hover:scale-[1.05] focus:outline-none focus:ring-2 focus:ring-[#8DA399]/30 disabled:opacity-70 disabled:pointer-events-none"
      >
        {loading ? (
          <Loader2 className="animate-spin" size={22} strokeWidth={2.25} aria-hidden />
        ) : (
          <Search size={20} strokeWidth={2.25} />
        )}
      </button>
    </>
  );

  const barWrapper = loading ? (
    <div
      className={`search-bar-rainbow-ring w-full ${fullWidth ? "" : "max-w-3xl"} shadow-sm rounded-full`}
    >
      <div className={innerBarClass}>{fields}</div>
    </div>
  ) : (
    <div className={innerBarClass}>{fields}</div>
  );

  return (
    <div className={`w-full flex flex-col items-center ${fullWidth ? "" : ""}`}>
      <form onSubmit={handleSubmit} className="w-full flex justify-center">
        {barWrapper}
      </form>
      {displayError ? (
        <p
          id={`${id}-error`}
          role="alert"
          className={`mt-3 text-sm text-[#B91C1C] text-center px-2 ${fullWidth ? "w-full" : "max-w-3xl w-full"}`}
        >
          {displayError}
        </p>
      ) : null}
    </div>
  );
}

export default SearchBar;
