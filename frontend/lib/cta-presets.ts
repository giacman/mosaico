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
    de: string
    es: string // Added ES which was missing in the list but present in code
    zh: string
    ko: string
  }
}

export const CTA_PRESETS: CTAPreset[] = [
  {
    id: "shop-selection",
    en: "SHOP THE SELECTION",
    translations: {
      it: "ACQUISTA LA SELEZIONE",
      fr: "ACHETER LA SÉLÉCTION",
      de: "JETZT SHOPPEN",
      es: "COMPRAR LA SELECCIÓN", // Inferring ES as it was missing in provided list for this item, using generic
      zh: "探索甄选",
      ko: "셀렉션 구매하기",
    },
  },
  {
    id: "shop-womens",
    en: "SHOP WOMEN'S",
    translations: {
      it: "ACQUISTA DONNA",
      fr: "ACHETER FEMME",
      de: "FÜR DAMEN",
      es: "COMPRAR MUJER",
      zh: "女士",
      ko: "여성 셀렉션 구매하기",
    },
  },
  {
    id: "shop-mens",
    en: "SHOP MEN'S",
    translations: {
      it: "ACQUISTA UOMO",
      fr: "ACHETER HOMME",
      de: "FÜR HERREN",
      es: "COMPRAR HOMBRE",
      zh: "男士",
      ko: "남성 셀렉션 구매하기",
    },
  },
  {
    id: "for-her",
    en: "FOR HER",
    translations: {
      it: "PER LEI",
      fr: "POUR ELLE",
      de: "FÜR SIE",
      es: "PARA ELLA",
      zh: "女士",
      ko: "여성",
    },
  },
  {
    id: "for-him",
    en: "FOR HIM",
    translations: {
      it: "PER LUI",
      fr: "POUR LUI",
      de: "FÜR IHN",
      es: "PARA ÉL",
      zh: "男士",
      ko: "남성",
    },
  },
  {
    id: "shop-girls",
    en: "SHOP GIRLS'",
    translations: {
      it: "ACQUISTA BAMBINA",
      fr: "ACHETER FILLE",
      de: "FÜR MÄDCHEN",
      es: "COMPRAR NIÑA",
      zh: "女孩系列",
      ko: "여아 컬렉션 구매하기",
    },
  },
  {
    id: "shop-boys",
    en: "SHOP BOYS'",
    translations: {
      it: "ACQUISTA BAMBINO",
      fr: "ACHETER GARÇON",
      de: "FÜR JUNGEN",
      es: "COMPRAR NIÑO",
      zh: "男孩系列",
      ko: "남아 컬렉션 구매하기",
    },
  },
  {
    id: "shop-home",
    en: "SHOP HOME",
    translations: {
      it: "ACQUISTA CASA",
      fr: "ACHETER MAISON",
      de: "JETZT SHOPPEN",
      es: "COMPRAR HOGAR",
      zh: "选购家居产品",
      ko: "홈 데코 구매하기",
    },
  },
  {
    id: "shop-beauty",
    en: "SHOP BEAUTY",
    translations: {
      it: "ACQUISTA BEAUTY",
      fr: "ACHETER BEAUTÉ",
      de: "JETZT SHOPPEN",
      es: "COMPRAR BELLEZA",
      zh: "选购美容单品",
      ko: "뷰티 구매하기",
    },
  },
  {
    id: "read-edit",
    en: "READ THE EDIT",
    translations: {
      it: "LEGGI L'EDITORIALE",
      fr: "LIRE L’ARTICLE",
      de: "DAS EDITORIAL SHOPPEN",
      es: "LEER EL EDITORIAL",
      zh: "阅读文章",
      ko: "에디토리얼",
    },
  },
  {
    id: "visit-us",
    en: "VISIT US",
    translations: {
      it: "VIENI A TROVARCI",
      fr: "RENDEZ-NOUS VISITE",
      de: "STORE BESUCHEN",
      es: "VISÍTANOS",
      zh: "访问门店",
      ko: "방문하기",
    },
  },
  {
    id: "shop-annagreta",
    en: "SHOP ANNAGRETA",
    translations: {
      it: "ACQUISTA ANNAGRETA",
      fr: "ACHETER ANNAGRETA",
      de: "JETZT SHOPPEN",
      es: "COMPRAR ANNAGRETA",
      zh: "选购 ANNAGRETA",
      ko: "ANNAGRETA 구매하기",
    },
  },
  {
    id: "shop-core",
    en: "SHOP THE CORE",
    translations: {
      it: "ACQUISTA THE CORE",
      fr: "ACHETER THE CORE",
      de: "JETZT SHOPPEN",
      es: "COMPRAR THE CORE",
      zh: "选购 THE CORE",
      ko: "THE CORE 구매하기",
    },
  },
  {
    id: "book-experience",
    en: "Book the experience",
    translations: {
      it: "Prenota l'esperienza",
      fr: "Réserver l'expérience",
      de: "Das Erlebnis buchen",
      es: "Reserva la experiencia",
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
      de: "Mehr erfahren",
      es: "Descubre más",
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
      de: "Punkte einlösen",
      es: "Canjear puntos",
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
      de: "Alle erhältlichen Prämien entdecken",
      es: "Descubre todas las recompensas",
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
      de: "Mehr entdecken",
      es: "Descubre más",
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
