/**
 * Section utilities - Single source of truth for section/component operations
 * Part of V2 multi-section implementation
 */

export interface SectionComponent {
  id?: number
  component_type: string
  component_index?: number
  generated_content?: string
  translations?: Record<string, string> | any[] // Can be normalized object or raw array from backend
  image_id?: number
  image?: {
    id: string
    url: string
    filename: string
  }
  section_key?: string
  section_order?: number
}

/**
 * Normalize translations into a plain { lang: text } map
 * Handles both backend array format and local object format
 */
export function normalizeTranslationsMap(input: any): Record<string, string> {
  if (!input) return {}

  const out: Record<string, string> = {}

  if (typeof input === "object" && !Array.isArray(input)) {
    Object.entries(input).forEach(([k, v]) => {
      if (v == null) return
      if (typeof v === "string") {
        out[String(k).toLowerCase()] = v
      } else if (typeof v === "object") {
        const lang = (v as any).language_code || k
        const text = (v as any).translated_content || (v as any).content || String(v)
        out[String(lang).toLowerCase()] = String(text)
      }
    })
  } else if (Array.isArray(input)) {
    input.forEach((it) => {
      if (it && typeof it === "object") {
        const lang = (it as any).language_code || (it as any).lang || (it as any).code
        const text = (it as any).translated_content || (it as any).content || (it as any).text
        if (lang && text) out[String(lang).toLowerCase()] = String(text)
      }
    })
  }

  return out
}

/**
 * Normalize a list of components for consistent usage across the app
 */
export function normalizeComponentList(list: any[]): any[] {
  return (list || []).map((c: any) => {
    const translations = normalizeTranslationsMap(c.translations)
    // Preserving the 'image' object if it exists for immediate UI preview
    return {
      ...c,
      generated_content: c.generated_content ?? "",
      translations,
      section_key: c.section_key || 'default',
      section_order: c.section_order ?? 0,
      image: c.image || undefined
    }
  })
}

export interface Section {
  key: string
  name: string
  components: string[]
  brief?: string  // Section-specific brief (used in V2)
}

/**
 * Find a component for a specific section with its index
 * Handles both section_key and section_order matching for backward compatibility
 */
export function findComponentForSection(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number,
  componentType: string,
  componentIndex: number = 1
): SectionComponent | undefined {
  const idx = componentIndex <= 0 ? 1 : componentIndex

  // 1. Try to find by section_key AND index
  const byKey = components.find(c =>
    c.component_type === componentType &&
    (c.component_index === idx || (c.component_index || 1) === idx) &&
    c.section_key === sectionKey
  )
  if (byKey) return byKey

  // 2. Try to find by section_order AND index (fallback)
  return components.find(c =>
    c.component_type === componentType &&
    (c.component_index === idx || (c.component_index || 1) === idx) &&
    c.section_order === sectionOrder
  )
}

/**
 * Ensure all sections have valid keys
 */
export function ensureSectionKeys(sections: Section[]): Section[] {
  return sections.map((section, idx) => ({
    ...section,
    key: section.key || `section_${idx + 1}`,
    name: section.name || `Section ${idx + 1}`,
    components: Array.isArray(section.components) ? section.components : []
  }))
}

/**
 * Check if section is the main section (cannot be removed)
 */
export function isMainSection(section: Section): boolean {
  return section.key === 'main' || section.name.toLowerCase() === 'main section'
}

/**
 * Find image component for a section
 */
export function findImageForSection(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number
): SectionComponent | undefined {
  return findComponentForSection(components, sectionKey, sectionOrder, 'image')
}

/**
 * Check if a section has an image uploaded
 */
export function sectionHasImage(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number
): boolean {
  const imageComponent = findImageForSection(components, sectionKey, sectionOrder)
  return !!(imageComponent?.image_id || imageComponent?.image)
}
