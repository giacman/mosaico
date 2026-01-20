/**
 * Shared language configuration for the application
 * Uses SVG flags from flagcdn.com for cross-platform compatibility
 */

export interface Language {
  value: string
  label: string
  flagUrl: string
  countryCode: string // ISO 3166-1 alpha-2 for flag lookup
}

// Map language codes to country codes for flag display
const LANG_TO_COUNTRY: Record<string, string> = {
  en: "gb", // English -> UK flag
  it: "it",
  fr: "fr",
  es: "es",
  de: "de",
  zh: "cn", // Chinese -> China flag
  ko: "kr", // Korean -> South Korea flag
  ja: "jp", // Japanese -> Japan flag
}

/**
 * Generate flag URL from country code using flagcdn.com
 * @param countryCode - ISO 3166-1 alpha-2 country code (lowercase)
 * @param width - Width in pixels (default 40). Valid widths: 20, 40, 80, 160, 320, 640, 1280, 2560
 */
export function getFlagUrl(countryCode: string, width: number = 40): string {
  // flagcdn.com only supports specific widths: 20, 40, 80, 160, 320, 640, 1280, 2560
  const validWidths = [20, 40, 80, 160, 320, 640, 1280, 2560]
  const closestWidth = validWidths.reduce((prev, curr) => 
    Math.abs(curr - width) < Math.abs(prev - width) ? curr : prev
  )
  return `https://flagcdn.com/w${closestWidth}/${countryCode.toLowerCase()}.png`
}

export const LANGUAGES: Language[] = [
  { value: "it", label: "Italian", countryCode: "it", flagUrl: getFlagUrl("it") },
  { value: "fr", label: "French", countryCode: "fr", flagUrl: getFlagUrl("fr") },
  { value: "es", label: "Spanish", countryCode: "es", flagUrl: getFlagUrl("es") },
  { value: "de", label: "German", countryCode: "de", flagUrl: getFlagUrl("de") },
  { value: "zh", label: "Chinese", countryCode: "cn", flagUrl: getFlagUrl("cn") },
  { value: "ko", label: "Korean", countryCode: "kr", flagUrl: getFlagUrl("kr") },
  { value: "ja", label: "Japanese", countryCode: "jp", flagUrl: getFlagUrl("jp") },
]

export const ENGLISH_LANGUAGE: Language = {
  value: "en",
  label: "English",
  countryCode: "gb",
  flagUrl: getFlagUrl("gb")
}

/**
 * Get language by value code
 */
export function getLanguage(value: string): Language | undefined {
  if (value === "en") return ENGLISH_LANGUAGE
  return LANGUAGES.find(lang => lang.value === value)
}

/**
 * Get flag URL for a language code
 */
export function getFlagUrlForLanguage(langCode: string, width: number = 40): string {
  const countryCode = LANG_TO_COUNTRY[langCode] || langCode
  return getFlagUrl(countryCode, width)
}
