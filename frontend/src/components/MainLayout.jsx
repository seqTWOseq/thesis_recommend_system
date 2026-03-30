import React from "react";
import SearchBar from "./SearchBar";

function MainLayout({
  onSearch,
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
    <main className="min-h-screen bg-[#F9F9F7] px-4 relative overflow-hidden">
      {/* Top section (image placeholder area) */}
      <section
        className="h-[50vh] relative bg-[#F9F9F7] bg-cover bg-center"
        style={backgroundStyle}
        aria-hidden="true"
      >
        {/* Soft placeholder texture while the real image is added later */}
        {!backgroundImageUrl ? (
          <>
            <div className="absolute inset-0 bg-gradient-to-br from-[#F9F9F7] to-[#E6EFEB]" />
            <div className="absolute inset-0 border border-dashed border-[#8DA399]/30" />
          </>
        ) : null}
      </section>

      {/* Bottom section */}
      <section className="h-[50vh] bg-[#F9F9F7] flex items-start justify-center">
        <div className="w-full mx-auto max-w-5xl pt-20 pb-6">
          {children ? children : null}
        </div>
      </section>

      {/* Search bar is anchored to the screen center (50vh boundary) */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-5xl px-4">
        <div className="relative flex justify-center">
          <h1 className="absolute -top-[74px] left-1/2 -translate-x-1/2 text-3xl sm:text-4xl font-semibold tracking-tight text-[#355548]">
            Find Thesis
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

