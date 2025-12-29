import {
  normalizeTranslationsMap,
  normalizeComponentList,
  findComponentForSection,
  ensureSectionKeys,
  isMainSection,
  normalizeImage,
  sectionHasImage,
  type SectionComponent,
  type Section,
} from '@/lib/section-utils'

describe('section-utils', () => {
  
  describe('normalizeImage', () => {
    it('should convert backend image to frontend format using gcs_public_url', () => {
      const backendImage = {
        id: 123,
        filename: 'test.jpg',
        gcs_path: 'gs://bucket/test.jpg',
        gcs_public_url: 'https://storage.googleapis.com/bucket/test.jpg',
      }
      
      const result = normalizeImage(backendImage)
      
      expect(result).toEqual({
        id: '123',
        url: 'https://storage.googleapis.com/bucket/test.jpg',
        filename: 'test.jpg',
      })
    })

    it('should fallback to url if gcs_public_url is null', () => {
      const image = {
        id: 456,
        filename: 'test2.png',
        gcs_path: 'gs://bucket/test2.png',
        gcs_public_url: null,
        url: 'https://example.com/test2.png',
      }
      
      const result = normalizeImage(image)
      
      expect(result.url).toBe('https://example.com/test2.png')
    })

    it('should fallback to gcs_path if no url fields', () => {
      const image = {
        id: 789,
        filename: 'test3.gif',
        gcs_path: 'gs://bucket/test3.gif',
        gcs_public_url: null,
      }
      
      const result = normalizeImage(image)
      
      expect(result.url).toBe('gs://bucket/test3.gif')
    })
  })

  describe('normalizeTranslationsMap', () => {
    it('should return empty object for null input', () => {
      expect(normalizeTranslationsMap(null)).toEqual({})
    })

    it('should handle object format', () => {
      const input = { IT: 'Ciao', FR: 'Bonjour' }
      const result = normalizeTranslationsMap(input)
      
      expect(result).toEqual({ it: 'Ciao', fr: 'Bonjour' })
    })

    it('should handle array format from backend', () => {
      const input = [
        { language_code: 'IT', translated_content: 'Ciao' },
        { language_code: 'FR', translated_content: 'Bonjour' },
      ]
      const result = normalizeTranslationsMap(input)
      
      expect(result).toEqual({ it: 'Ciao', fr: 'Bonjour' })
    })

    it('should lowercase language codes', () => {
      const input = { IT: 'test', FR: 'test', DE: 'test' }
      const result = normalizeTranslationsMap(input)
      
      expect(Object.keys(result)).toEqual(['it', 'fr', 'de'])
    })
  })

  describe('findComponentForSection', () => {
    const components: SectionComponent[] = [
      { component_type: 'title', section_key: 'main', section_order: 0, generated_content: 'Main Title' },
      { component_type: 'body', section_key: 'main', section_order: 0, generated_content: 'Main Body' },
      { component_type: 'title', section_key: 'section_2', section_order: 1, generated_content: 'Section 2 Title' },
      { component_type: 'body', section_key: 'section_2', section_order: 1, generated_content: 'Section 2 Body' },
    ]

    it('should find component by section_key', () => {
      const result = findComponentForSection(components, 'main', 0, 'title')
      expect(result?.generated_content).toBe('Main Title')
    })

    it('should find component in second section', () => {
      const result = findComponentForSection(components, 'section_2', 1, 'body')
      expect(result?.generated_content).toBe('Section 2 Body')
    })

    it('should return undefined for non-existent component', () => {
      const result = findComponentForSection(components, 'main', 0, 'cta')
      expect(result).toBeUndefined()
    })

    it('should fallback to section_order if section_key not found', () => {
      const componentsWithoutKey: SectionComponent[] = [
        { component_type: 'title', section_order: 0, generated_content: 'Fallback Title' },
      ]
      
      const result = findComponentForSection(componentsWithoutKey, 'unknown', 0, 'title')
      expect(result?.generated_content).toBe('Fallback Title')
    })
  })

  describe('ensureSectionKeys', () => {
    it('should add keys to sections without keys', () => {
      const sections: Section[] = [
        { key: '', name: 'First', components: ['title'] },
        { key: '', name: 'Second', components: ['body'] },
      ]
      
      const result = ensureSectionKeys(sections)
      
      expect(result[0].key).toBe('section_1')
      expect(result[1].key).toBe('section_2')
    })

    it('should preserve existing keys', () => {
      const sections: Section[] = [
        { key: 'main', name: 'Main', components: ['title'] },
        { key: 'promo', name: 'Promo', components: ['body'] },
      ]
      
      const result = ensureSectionKeys(sections)
      
      expect(result[0].key).toBe('main')
      expect(result[1].key).toBe('promo')
    })
  })

  describe('isMainSection', () => {
    it('should return true for section with key "main"', () => {
      const section: Section = { key: 'main', name: 'Whatever', components: [] }
      expect(isMainSection(section)).toBe(true)
    })

    it('should return true for section named "Main Section"', () => {
      const section: Section = { key: 'section_1', name: 'Main Section', components: [] }
      expect(isMainSection(section)).toBe(true)
    })

    it('should return false for other sections', () => {
      const section: Section = { key: 'section_2', name: 'Promo Section', components: [] }
      expect(isMainSection(section)).toBe(false)
    })
  })

  describe('sectionHasImage', () => {
    it('should return true if component has image_id', () => {
      const components: SectionComponent[] = [
        { component_type: 'image', section_key: 'main', section_order: 0, image_id: 123 },
      ]
      
      expect(sectionHasImage(components, 'main', 0)).toBe(true)
    })

    it('should return true if component has image object', () => {
      const components: SectionComponent[] = [
        { 
          component_type: 'image', 
          section_key: 'main', 
          section_order: 0, 
          image: { id: '123', url: 'https://example.com/img.jpg', filename: 'img.jpg' }
        },
      ]
      
      expect(sectionHasImage(components, 'main', 0)).toBe(true)
    })

    it('should return false if no image component exists', () => {
      const components: SectionComponent[] = [
        { component_type: 'title', section_key: 'main', section_order: 0 },
      ]
      
      expect(sectionHasImage(components, 'main', 0)).toBe(false)
    })
  })

  describe('normalizeComponentList', () => {
    it('should normalize translations in component list', () => {
      const components = [
        { 
          component_type: 'title',
          generated_content: 'Hello',
          translations: [{ language_code: 'IT', translated_content: 'Ciao' }]
        }
      ]
      
      const result = normalizeComponentList(components)
      
      expect(result[0].translations).toEqual({ it: 'Ciao' })
    })

    it('should set default section_key if missing', () => {
      const components = [{ component_type: 'title' }]
      const result = normalizeComponentList(components)
      
      expect(result[0].section_key).toBe('default')
    })

    it('should set default section_order if missing', () => {
      const components = [{ component_type: 'title' }]
      const result = normalizeComponentList(components)
      
      expect(result[0].section_order).toBe(0)
    })
  })
})

