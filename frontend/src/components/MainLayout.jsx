import React from "react";
import SearchBar from "./SearchBar";
import findThesisLogoUrl from "../../img/FindThesisLogo.png";

function MainLayout({
  onSearch,
  onLogoClick,
  backgroundImageUrl,
  children,
  searchLoading = false,
  searchError = null,
  onDismissSearchError,
}) {
  const backgroundStyle = backgroundImageUrl
    ? { backgroundImage: `url(${backgroundImageUrl})` }
    : undefined;

  return (
    <main className="min-h-screen bg-[#DBD3C7] px-4 relative overflow-hidden">
      {/* Top section (image placeholder area) */}
      <section
        // className="h-[50vh] relative bg-[#DBD3C7] bg-cover bg-center"
        style={backgroundStyle}
        aria-hidden="true"
      >
        {/* Soft placeholder texture while the real image is added later */}
        {!backgroundImageUrl ? (
          <>
            <div className="absolute inset-0 bg-[#DBD3C7]" />
            <div className="absolute inset-0 border border-dashed border-[#8DA399]/30" />
          </>
        ) : null}
      </section>

      {/* Bottom section */}
      <section className="h-[50vh] bg-[#DBD3C7] flex items-start justify-center">
        <div className="w-full mx-auto max-w-5xl pt-20 pb-6">
          {children ? children : null}
        </div>
      </section>

      {/* Search bar is anchored to the screen center (50vh boundary) */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-5xl px-4">
        <div className="relative flex justify-center">
          <h1 className="absolute -top-[86px] left-1/2 -translate-x-1/2 m-0 sm:-top-[94px]">
            <button
              type="button"
              onClick={onLogoClick}
              className="m-0 block cursor-pointer border-0 bg-transparent p-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#8DA399]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#DBD3C7] rounded-md"
              aria-label="홈으로 이동 · 새로고침"
            >
              <img
                src={findThesisLogoUrl}
                alt=""
                className="pointer-events-none block h-[3.25rem] w-auto sm:h-[3.9rem]"
              />
            </button>
          </h1>
          <SearchBar
            onSearch={onSearch}
            loading={searchLoading}
            apiError={searchError}
            onDismissApiError={onDismissSearchError}
          />
        </div>
      </div>
    </main>
  );
}

export default MainLayout;

