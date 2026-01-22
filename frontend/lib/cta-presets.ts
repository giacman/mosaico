/**
 * CTA Presets with pre-translated content
 * These are commonly used CTAs with verified translations for all supported languages
 */

export interface CTAPreset {
  id: string
  en: string
  translations: {
    it: string
    fr: string
    es: string
    de: string
    zh: string
    ko: string
  }
}

export const CTA_PRESETS: CTAPreset[] = [
  {
    id: "book-experience",
    en: "Book the experience",
    translations: {
      it: "Prenota l'esperienza",
      fr: "Réserver l'expérience",
      es: "Reserva la experiencia",
      de: "Das Erlebnis buchen",
      zh: "预定体验",
      ko: "예약하기",
    },
  },
  {
    id: "discover-more",
    en: "Discover more",
    translations: {
      it: "Scopri di più",
      fr: "En savoir plus",
      es: "Descubre más",
      de: "Mehr erfahren",
      zh: "探索更多",
      ko: "더보기",
    },
  },
  {
    id: "redeem-now",
    en: "Redeem now",
    translations: {
      it: "Converti i tuoi punti",
      fr: "Échangez vos points",
      es: "Canjear puntos",
      de: "Punkte einlösen",
      zh: "立即兑换",
      ko: "포인트 전환",
    },
  },
  {
    id: "explore-rewards",
    en: "Explore All Rewards",
    translations: {
      it: "Scopri tutti i reward",
      fr: "Voir toutes les récompenses disponibles",
      es: "Descubre todas las recompensas",
      de: "Alle erhältlichen Prämien entdecken",
      zh: "查看所有可用奖励",
      ko: "모든 리워드 보기",
    },
  },
  {
    id: "discover-reward",
    en: "Discover the Reward",
    translations: {
      it: "Scopri il reward",
      fr: "Découvrir la récompense",
      es: "Descubre más",
      de: "Mehr entdecken",
      zh: "探索奖励",
      ko: "리워드 자세히 보기",
    },
  },
]

/**
 * Get a CTA preset by ID
 */
export function getCTAPreset(id: string): CTAPreset | undefined {
  return CTA_PRESETS.find((preset) => preset.id === id)
}

/**
 * Get the translation for a specific language from a preset
 * Returns uppercase version for display consistency
 */
export function getPresetTranslation(preset: CTAPreset, langCode: string): string {
  if (langCode === "en") {
    return preset.en.toUpperCase()
  }
  const lang = langCode.toLowerCase() as keyof CTAPreset["translations"]
  return (preset.translations[lang] || preset.en).toUpperCase()
}
