const MIN_VALID_LENGTH = 10;

/** Valid chars for length: Korean, English, digits, spaces (internal). */
const VALID_CHAR_REGEX = /[^a-zA-Z0-9가-힣\s]/g;

export const SEARCH_VALIDATION_MESSAGES = {
  EMPTY: "Please enter a search term.",
  TOO_SHORT: "Please enter at least 10 valid characters.",
};

/**
 * @param {string} rawInput
 * @returns {{ ok: true, queryForApi: string } | { ok: false, code: string, message: string }}
 */
export function validateSearchInput(rawInput) {
  if (typeof rawInput !== "string") {
    return {
      ok: false,
      code: "EMPTY",
      message: SEARCH_VALIDATION_MESSAGES.EMPTY,
    };
  }

  if (rawInput.trim().length === 0) {
    return {
      ok: false,
      code: "EMPTY",
      message: SEARCH_VALIDATION_MESSAGES.EMPTY,
    };
  }

  const processedInput = rawInput.trimEnd();
  const lengthCheckText = processedInput.replace(VALID_CHAR_REGEX, "");

  if (lengthCheckText.trim().length === 0) {
    return {
      ok: false,
      code: "EMPTY",
      message: SEARCH_VALIDATION_MESSAGES.EMPTY,
    };
  }

  if (lengthCheckText.length < MIN_VALID_LENGTH) {
    return {
      ok: false,
      code: "TOO_SHORT",
      message: SEARCH_VALIDATION_MESSAGES.TOO_SHORT,
    };
  }

  return { ok: true, queryForApi: rawInput.trim() };
}
