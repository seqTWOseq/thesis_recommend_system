import React, {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

function parseTitleAbstract(pageContent) {
  const content = typeof pageContent === "string" ? pageContent : "";

  // Extract Title between "Title:" and "Abstract:"
  const titleMatch = content.match(/Title:\s*(.*?)\s*Abstract:/s);
  const title = titleMatch?.[1]?.trim() || "Untitled";

  // Extract Abstract after "Abstract:"
  const abstractMatch = content.match(/Abstract:\s*([\s\S]*)$/s);
  const abstract = abstractMatch?.[1]?.trim() || "No abstract provided.";

  return { title, abstract };
}

function formatCategories(categories) {
  if (!Array.isArray(categories)) return "-";
  const tokens = categories
    .flatMap((chunk) =>
      typeof chunk === "string"
        ? chunk
            .split(/\s+/)
            .map((t) => t.trim())
            .filter(Boolean)
        : [],
    )
    .filter(Boolean);
  return tokens.length ? tokens.join(", ") : "-";
}

function formatSimilarity(similarity) {
  const n = typeof similarity === "number" ? similarity : Number(similarity);
  if (!Number.isFinite(n)) return "0.0000";
  return n.toFixed(4);
}

function ResultItem({ item, variant = "list" }) {
  const categoriesText = useMemo(
    () => formatCategories(item?.categories),
    [item],
  );
  const { title, abstract } = useMemo(
    () => parseTitleAbstract(item?.page_content),
    [item?.page_content],
  );

<<<<<<< HEAD
  const externalUrls = useMemo(() => {
    // Prefer explicit URL if provided
    if (item?.url && typeof item.url === "string") {
      return { view: item.url, pdf: null };
    }

    // Try to derive from arXiv id formats
    const rawId = String(item?.id || "").trim();
    if (!rawId) return { view: null, pdf: null };

    // Accept common forms: "2006.04515", "2006.04515v2", "arXiv:2006.04515", "arXiv:2006.04515v2"
    const arxivMatch =
      rawId.match(/^arXiv:(?<core>\d{4}\.\d{4,5}(v\d+)?)$/i) ||
      rawId.match(/^(?<core>\d{4}\.\d{4,5}(v\d+)?)$/);

    if (arxivMatch?.groups?.core) {
      const core = arxivMatch.groups.core;
      return {
        view: `https://arxiv.org/abs/${core}`,
        pdf: `https://arxiv.org/pdf/${core}.pdf`,
      };
    }

    return { view: null, pdf: null };
  }, [item?.id, item?.url]);

=======
>>>>>>> main
  const formattedDate = useMemo(() => {
    if (!item?.update_date) return "-";

    // DB에서 넘어온 타임스탬프 값
    let timestamp = item.update_date;

    // 타임스탬프가 초 단위(10자리 이하, 대략 100억 미만)인지 확인하여 밀리초 단위로 변환
    if (timestamp < 10000000000) {
      timestamp = timestamp * 1000;
    }

    const date = new Date(timestamp);
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  }, [item?.update_date]);

  const isHighlight = variant === "highlight";

  return (
    <article
      className={
        "w-full rounded-xl border p-4 shadow-sm transition-colors " +
        (isHighlight
          ? "border-[#8DA399]/50 bg-[#8DA399]/10"
          : "border-[#E5E7EB] bg-white/70")
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs text-[#6B7280]">
            ID:{" "}
            <span className="font-medium text-[#374151]">
              {item?.id || "-"}
            </span>
          </p>
          <p className="text-xs text-[#6B7280] mt-1">
            Date:{" "}
            <span className="font-medium text-[#374151]">{formattedDate}</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-[#8DA399]">
            Similarity:{" "}
            <span className="font-semibold text-[#355548]">
              {formatSimilarity(item?.similarity)}
            </span>
          </p>
          <p className="text-xs text-[#6B7280]">{categoriesText}</p>
          {externalUrls.view ? (
            <div className="mt-2 flex justify-end gap-3">
              <a
                href={externalUrls.pdf || externalUrls.view}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-[#4F46E5] hover:underline"
              >
                원문 보기
              </a>
              {externalUrls.pdf && (
                <a
                  href={externalUrls.view}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-[#4F46E5]/80 hover:underline"
                >
                  초록
                </a>
              )}
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-3 space-y-3">
        <div>
          <p className="text-xs font-semibold tracking-wide text-[#8DA399]">
            Title
          </p>
<<<<<<< HEAD
          {externalUrls.pdf || externalUrls.view ? (
            <a
              href={externalUrls.pdf || externalUrls.view}
              target="_blank"
              rel="noreferrer"
              className={
                "mt-1 inline-block font-semibold text-[#374151] hover:underline " +
                (isHighlight ? "text-base sm:text-lg" : "text-base")
              }
            >
              {title}
            </a>
          ) : (
            <h3
              className={
                "mt-1 font-semibold text-[#374151] " +
                (isHighlight ? "text-base sm:text-lg" : "text-base")
              }
            >
              {title}
            </h3>
          )}
=======
          <h3
            className={
              "mt-1 font-semibold text-[#374151] " +
              (isHighlight ? "text-base sm:text-lg" : "text-base")
            }
          >
            {title}
          </h3>
>>>>>>> main
        </div>

        <div>
          <p className="text-xs font-semibold tracking-wide text-[#8DA399]">
            Abstract
          </p>
          <p className="mt-1 text-sm text-[#6B7280] whitespace-pre-line break-words">
            {abstract}
          </p>
        </div>
      </div>
    </article>
  );
}

const MemoResultItem = memo(ResultItem);

function HighlightList({ items }) {
  if (!items || items.length === 0) {
    return (
      <div className="w-full rounded-xl border border-dashed border-[#8DA399]/40 bg-white/50 p-4">
        <p className="text-sm text-[#374151]/70">하이라이트 결과가 없습니다.</p>
      </div>
    );
  }

  return (
    <section className="w-full">
      <div className="mb-3">
        <p className="text-sm font-semibold text-[#355548]">Top 5</p>
        <p className="text-xs text-[#6B7280]">유사도 상위 5개 결과</p>
      </div>
      <div className="flex w-full flex-col gap-3">
        {items.map((item) => (
          <MemoResultItem key={item?.id} item={item} variant="highlight" />
        ))}
      </div>
    </section>
  );
}

function ResultList({ items }) {
  const PAGE_SIZE = 10;
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const sentinelRef = useRef(null);
  const guardRef = useRef(false);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [items]);

  const canLoadMore = visibleCount < (items?.length || 0);

  const loadMore = useCallback(() => {
    setVisibleCount((prev) => Math.min(prev + PAGE_SIZE, items.length));
  }, [items]);

  useEffect(() => {
    if (!canLoadMore) return;
    const el = sentinelRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (!first?.isIntersecting) return;
        if (guardRef.current) return;
        guardRef.current = true;
        loadMore();
      },
      { root: null, threshold: 0.01 },
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
    };
  }, [canLoadMore, loadMore, visibleCount]);

  useEffect(() => {
    guardRef.current = false;
  }, [visibleCount]);

  if (!items || items.length === 0) {
    return (
      <p className="text-[#374151]/70 text-sm sm:text-base text-center">
        검색 결과가 없습니다.
      </p>
    );
  }

  const visibleItems = items.slice(0, visibleCount);

  return (
    <section className="w-full mt-6">
      <div className="mb-3">
        <p className="text-sm font-semibold text-[#355548]">Results</p>
        <p className="text-xs text-[#6B7280]">
          {visibleItems.length} / {items.length}
        </p>
      </div>

      <ul className="w-full space-y-3">
        {visibleItems.map((item) => (
          <li key={item?.id}>
            <MemoResultItem item={item} />
          </li>
        ))}
      </ul>

      <div ref={sentinelRef} className="h-2" aria-hidden="true" />

      {!canLoadMore ? (
        <p className="mt-3 text-xs text-[#6B7280] text-center">
          더 이상 결과가 없습니다.
        </p>
      ) : null}
    </section>
  );
}

export default function ThesisResults({ results }) {
  const normalized = useMemo(() => {
    if (!Array.isArray(results)) return [];
    // Ensure "Top" items are truly the highest similarity.
    const sorted = [...results].sort((a, b) => {
      const aScore = Number(a?.similarity);
      const bScore = Number(b?.similarity);
      return (
        (Number.isFinite(bScore) ? bScore : -Infinity) -
        (Number.isFinite(aScore) ? aScore : -Infinity)
      );
    });
    return sorted.slice(0, 100);
  }, [results]);

  const highlightItems = useMemo(() => normalized.slice(0, 5), [normalized]);
  const restItems = useMemo(() => normalized.slice(5, 100), [normalized]);

  return (
    <div className="w-full">
      <HighlightList items={highlightItems} />
      <ResultList items={restItems} />
    </div>
  );
}

export { HighlightList, ResultList, ResultItem };
