/**
 * Section utilities - Single source of truth for section/component operations
 * Part of V2 multi-section implementation
 */

/**
 * Uploaded image type used in frontend
 */
export interface UploadedImage {
  id: string
  url: string
  filename: string
  uploading?: boolean
}

/**
 * Backend image type (from API)
 */
export interface BackendImage {
  id: number
  project_id?: number
  filename: string
  gcs_path: string
  gcs_public_url: string | null
  uploaded_at?: string
}

/**
 * Normalize a backend image to frontend UploadedImage format
 * Handles the gcs_public_url -> url transformation
 */
export function normalizeImage(image: BackendImage | any): UploadedImage {
  return {
    id: String(image.id),
    url: image.gcs_public_url || image.url || image.gcs_path || '',
    filename: image.filename || 'image'
  }
}

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
 * Find a component for a specific section
 * 
 * Strategy: Look up by section_key + type + component_index
 * Falls back to section_order for legacy data without section_key
 */
export function findComponentForSection(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number,
  componentType: string,
  componentIndex: number = 1
): SectionComponent | undefined {
  // Primary: find by section_key + type + component_index
  const byKeyAndIndex = components.find(c =>
    c.component_type === componentType &&
    c.section_key === sectionKey &&
    (c.component_index || 1) === componentIndex
  )
  if (byKeyAndIndex) return byKeyAndIndex

  // Secondary: find by section_key + type (for components without explicit index)
  const byKey = components.find(c =>
    c.component_type === componentType &&
    c.section_key === sectionKey
  )
  if (byKey) return byKey

  // Fallback: find by section_order + type + component_index (for legacy data)
  const byOrderAndIndex = components.find(c =>
    c.component_type === componentType &&
    c.section_order === sectionOrder &&
    (c.component_index || 1) === componentIndex
  )
  if (byOrderAndIndex) return byOrderAndIndex

  // Last resort: section_order + type
  return components.find(c =>
    c.component_type === componentType &&
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
