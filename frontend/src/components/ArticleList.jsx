import React from "react";

function ArticleList({ articles }) {
  if (!articles || articles.length === 0) {
    return <p>검색 결과가 없습니다.</p>;
  }

  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {articles.map((article, idx) => (
        <li key={idx} style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "1rem", marginBottom: "0.75rem" }}>
          <h3 style={{ margin: "0 0 0.5rem" }}>{article.title}</h3>
          <p style={{ margin: "0 0 0.5rem", color: "#555" }}>{article.abstract}</p>
          <span style={{ fontSize: "0.85rem", color: "#888" }}>유사도: {article.score}</span>
        </li>
      ))}
    </ul>
  );
}

export default ArticleList;
