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
            {article.snippet || article.abstract}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="text-sm text-[#8DA399] inline-block">
              유사도: {article.score}
            </span>
            {article.url ? (
              <a
                href={article.url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-[#4F46E5] hover:underline"
              >
                원문 보기
              </a>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default ArticleList;
