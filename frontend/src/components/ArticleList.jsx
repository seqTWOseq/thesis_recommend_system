import React from "react";

function ArticleList({ articles }) {
  if (!articles || articles.length === 0) {
    return (
      <p className="text-[#374151]/70 text-sm sm:text-base text-center">
        검색 결과가 없습니다.
      </p>
    );
  }

  return (
    <ul className="w-full">
      {articles.map((article, idx) => (
        <li
          key={idx}
          className="mb-3 last:mb-0 rounded-xl border border-[#E5E7EB] bg-white/70 p-4 shadow-sm"
        >
          <h3 className="font-semibold text-[#374151] text-base sm:text-lg">
            {article.title}
          </h3>
          <p className="text-[#6B7280] text-sm sm:text-[0.95rem] mt-2">
            {article.abstract}
          </p>
          <span className="text-sm text-[#8DA399] inline-block mt-3">
            유사도: {article.score}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default ArticleList;
