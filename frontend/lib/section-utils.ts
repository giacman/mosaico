/**
 * Section utilities - Single source of truth for section/component operations
 * Part of V2 multi-section implementation
 */

export interface SectionComponent {
  id?: number
  component_type: string
  component_index?: number
  generated_content?: string
  translations?: Record<string, string>
  image_id?: number
  image?: {
    id: string
    url: string
    filename: string
  }
  section_key?: string
  section_order?: number
}

export interface Section {
  key: string
  name: string
  components: string[]
  brief?: string  // Section-specific brief (used in V2)
}

/**
 * Find a component for a specific section
 * Handles both section_key and section_order matching for backward compatibility
 */
export function findComponentForSection(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number,
  componentType: string
): SectionComponent | undefined {
  // Prefer exact section_key match
  const exactMatch = components.find(c =>
    c.component_type === componentType &&
    c.section_key === sectionKey
  )
  
  if (exactMatch) return exactMatch
  
  // Fallback to section_order match (backward compatibility)
  return components.find(c =>
    c.component_type === componentType &&
    c.section_order === sectionOrder
  )
}

/**
 * Find all components for a specific section
 */
export function findComponentsForSection(
  components: SectionComponent[],
  sectionKey: string,
  sectionOrder: number
): SectionComponent[] {
  return components.filter(c =>
    c.section_key === sectionKey || c.section_order === sectionOrder
  )
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

/**
 * Get sections that are missing images
 */
export function getSectionsMissingImages(
  sections: Section[],
  components: SectionComponent[]
): Section[] {
  return sections.filter((section, idx) => {
    // Skip header section (no image required)
    if (section.key === 'header') return false
    
    // Check if section has image component in structure
    const hasImageInStructure = section.components.includes('image')
    if (!hasImageInStructure) return false
    
    // Check if image is actually uploaded
    return !sectionHasImage(components, section.key, idx)
  })
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
 * Create a new section with default components
 */
export function createNewSection(index: number, name?: string): Section {
  return {
    key: `section_${index}`,
    name: name || `Section ${index}`,
    components: ['image', 'title', 'body', 'cta'],
    brief: ''
  }
}

/**
 * Check if section is the main section (cannot be removed)
 */
export function isMainSection(section: Section): boolean {
  return section.key === 'main' || section.name.toLowerCase() === 'main section'
}

/**
 * Check if section is the header section (special handling)
 */
export function isHeaderSection(section: Section): boolean {
  return section.key === 'header'
}

