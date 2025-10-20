"use client"

import { useState } from "react"
import { Sparkles, Loader2, Copy, Check, Edit2, Languages, RefreshCw, FileCode } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import { generateContent } from "@/actions/generate"
import { batchTranslate } from "@/actions/translate"
import { generateHandlebar } from "@/actions/export"
import { saveGeneratedComponents } from "@/actions/components"
import { useNotifications } from "./notifications-provider"
import { Component as SavedComponent } from "@/actions/projects"
import { useEffect } from "react"

const LANGUAGES = [
  { value: "it", label: "Italian" },
  { value: "de", label: "German" },
  { value: "fr", label: "French" },
  { value: "es", label: "Spanish" },
  { value: "pt", label: "Portuguese" },
  { value: "ru", label: "Russian" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
  { value: "ar", label: "Arabic" },
  { value: "nl", label: "Dutch" }
]

interface ContentGeneratorProps {
  projectId: number
  brief: string
  tone: string
  structure: Array<{ component: string; count: number }>
  targetLanguages: string[]
  onLanguagesChange?: (languages: string[]) => void
  imageUrls?: string[]
  savedComponents?: SavedComponent[]
  userName?: string
}

interface GeneratedComponent {
  key: string
  label: string
  content: string
  editing: boolean
}

export function ContentGenerator({
  projectId,
  brief,
  tone,
  structure,
  targetLanguages,
  onLanguagesChange,
  imageUrls = [],
  savedComponents = [],
  userName = "Unknown user"
}: ContentGeneratorProps) {
  const { addNotification } = useNotifications()
  const [isGenerating, setIsGenerating] = useState(false)
  const [components, setComponents] = useState<GeneratedComponent[]>([])
  const [isTranslating, setIsTranslating] = useState(false)
  const [translations, setTranslations] = useState<Record<string, Record<string, string>>>({})
  const [temperature, setTemperature] = useState(0.7)
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  // Load saved components on mount
  useEffect(() => {
    if (savedComponents.length > 0) {
      // Convert saved components from backend to display format
      const loadedComponents: GeneratedComponent[] = savedComponents.map(comp => {
        const key = comp.component_index 
          ? `${comp.component_type}_${comp.component_index}`
          : comp.component_type
        
        return {
          key,
          label: formatLabel(key),
          content: comp.generated_content || "",
          editing: false
        }
      })
      
      setComponents(loadedComponents)
      
      // Load translations
      const loadedTranslations: Record<string, Record<string, string>> = {}
      savedComponents.forEach(comp => {
        const key = comp.component_index 
          ? `${comp.component_type}_${comp.component_index}`
          : comp.component_type
        
        if (comp.translations.length > 0) {
          loadedTranslations[key] = {}
          comp.translations.forEach(trans => {
            loadedTranslations[key][trans.language_code] = trans.translated_content
          })
        }
      })
      
      if (Object.keys(loadedTranslations).length > 0) {
        setTranslations(loadedTranslations)
      }
    }
  }, [savedComponents])

  // Helper function to save components to database with visual feedback
  const saveComponentsToDatabase = async (componentsToSave: GeneratedComponent[], translationsToSave: Record<string, Record<string, string>>) => {
    setIsSaving(true)
    try {
      // Convert to backend format
      const savedComponents = componentsToSave.map(comp => {
        // Extract component type and index from key (e.g., "body_1" -> type: "body", index: 1)
        const match = comp.key.match(/^(.+?)_(\d+)$/)
        const componentType = match ? match[1] : comp.key
        const componentIndex = match ? parseInt(match[2]) : undefined

        return {
          component_type: componentType,
          component_index: componentIndex,
          generated_content: comp.content,
          translations: translationsToSave[comp.key] || {}
        }
      })

      const result = await saveGeneratedComponents(projectId, savedComponents)
      
      if (!result.success) {
        console.error("Failed to save components:", result.error)
        // Don't show error toast to avoid annoying the user
        // The content is still in memory and usable
      }
    } catch (error) {
      console.error("Error saving components:", error)
    } finally {
      // Small delay so user sees the "Saved" indicator
      setTimeout(() => setIsSaving(false), 500)
    }
  }
  
  const formatLabel = (key: string): string => {
    return key
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  const handleGenerate = async () => {
    if (!brief.trim()) {
      toast.error("Please enter a creative brief first")
      return
    }

    if (structure.length === 0) {
      toast.error("Please select at least one email component")
      return
    }

    setIsGenerating(true)
    try {
      // Determine if structure contains Body (narratives need Pro quality)
      const hasBody = structure.some(s => s.component === 'body')
      const totalComponents = structure.reduce((sum, s) => sum + s.count, 0)
      const hasImage = imageUrls.length > 0
      const isComplexStructure = totalComponents >= 5 // 5+ components = complex
      
      // Use Flash ONLY for: image + complex structure + NO body
      // Flash tends to use bullet points for bodies, Pro is better for narratives
      const shouldUseFlash = hasImage && isComplexStructure && !hasBody
      
      if (shouldUseFlash) {
        console.log("⚡ Using Flash model: Image + complex structure (no body)", {
          totalComponents,
          hasImage,
          hasBody,
          structure: structure.map(s => `${s.component}(${s.count})`)
        })
        toast.info("⚡ Using Flash model for fast generation")
      } else if (hasImage && isComplexStructure && hasBody) {
        console.log("🎯 Using Pro model: Complex structure with body requires narrative quality", {
          totalComponents,
          hasImage,
          hasBody,
          structure: structure.map(s => `${s.component}(${s.count})`)
        })
      }
      
      let result = await generateContent({
        text: brief,
        count: 1, // Generate 1 variation
        tone: tone,
        content_type: "newsletter",
        structure: structure,
        image_url: imageUrls[0], // Use first image if available
        temperature: temperature,
        use_flash: shouldUseFlash // Use Flash for complex generation with images
      })

      // Automatic retry with Flash if Pro fails with JSON errors
      if (!result.success && !shouldUseFlash && hasImage && isComplexStructure) {
        const errorMsg = result.error || ""
        const isJsonError = errorMsg.includes("500") || errorMsg.includes("Failed to generate")
        
        if (isJsonError) {
          console.log("🔄 Pro failed, retrying with Flash as fallback...")
          toast.warning("⚠️ Retrying with Flash model for better stability...")
          
          result = await generateContent({
            text: brief,
            count: 1,
            tone: tone,
            content_type: "newsletter",
            structure: structure,
            image_url: imageUrls[0],
            temperature: temperature,
            use_flash: true // Force Flash on retry
          })
          
          if (result.success) {
            toast.success("✅ Generation succeeded with Flash fallback!")
          }
        }
      }

      if (result.success && result.data) {
        // Convert first (and only) variation to components
        const firstVariation = result.data.variations[0]
        const generatedComponents: GeneratedComponent[] = Object.entries(firstVariation).map(
          ([key, content]) => {
            // Normalize CTAs to UPPERCASE for brand consistency
            const isCTA = key.toLowerCase().includes('cta')
            return {
              key,
              label: formatLabel(key),
              content: isCTA ? (content as string).toUpperCase() : (content as string),
              editing: false
            }
          }
        )
        
        setComponents(generatedComponents)
        toast.success("Content generated successfully!")
        
        // Auto-save to database
        await saveComponentsToDatabase(generatedComponents, {})
        
        // Add persistent notification for team handoff
        addNotification({
          type: "success",
          title: "Content Generated",
          message: `AI has generated ${generatedComponents.length} components by ${userName}. Content team can now review for quality.`
        })
      } else {
        const errorMsg = result.error || "Failed to generate content"
        console.error("Generation failed:", errorMsg)
        toast.error(`Error: ${errorMsg}`)
      }
    } catch (error) {
      console.error("Error generating content:", error)
      const errorMessage = error instanceof Error ? error.message : "Unknown error"
      toast.error(`Failed to generate: ${errorMessage}`)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRegenerateAll = async () => {
    // Store if translations existed before regenerating
    const hadTranslations = Object.keys(translations).length > 0
    const previousLanguages = targetLanguages.length > 0 ? [...targetLanguages] : []
    
    // Regenerate content (this updates the components state)
    await handleGenerate()
    
    // If translations existed, automatically regenerate them
    // We need to wait for the state to update before translating
    if (hadTranslations && previousLanguages.length > 0) {
      // Use a small delay to ensure React state has propagated
      setTimeout(async () => {
        toast.info("🔄 Rigenerando anche le traduzioni...")
        await handleTranslate()
      }, 500)
    }
  }

  const handleRegenerateSingle = async (index: number) => {
    const component = components[index]
    setRegeneratingIndex(index)
    
    try {
      // Extract component type and count from the component key
      const componentType = component.key.replace(/_\d+$/, '') // Remove trailing number if exists
      
      // Build context from ALL existing components so AI knows the full email structure
      const existingContext = components
        .map(c => `${c.label}: "${c.content}"`)
        .join('\n')
      
      // Add context about previous version to encourage different output
      const randomSeed = Math.random().toString(36).substring(7)
      const timestamp = Date.now()
      const iteration = Math.floor(Math.random() * 1000)
      
      // For short components (CTAs), use even more aggressive variation prompts
      const isShortComponent = component.content.length < 30
      const variationInstruction = isShortComponent 
        ? `
🚨 CRITICAL: This is a SHORT CTA (${component.content.length} chars). 
You MUST use completely DIFFERENT words. Do NOT use any words from: "${component.content}"
Try these alternative approaches:
- Different action verb (if current is "SHOP", try "DISCOVER", "EXPLORE", "GET", "FIND")
- Different structure (if current is "SHOP X", try "X NOW", "GET X", "FIND YOUR X")
- Different focus (category vs. action vs. urgency)

FORBIDDEN: Do not repeat "${component.content}" or use similar words.
ITERATION #${iteration} - Generate variation #${iteration} with fresh creativity.
`
        : `Generate a completely different version with new wording and approach.`
      
      const enhancedBrief = `${brief}

FULL EMAIL CONTEXT (for reference):
${existingContext}

CRITICAL INSTRUCTION - You MUST regenerate ONLY the "${component.label}" component:
Current version (STRICTLY FORBIDDEN TO REPEAT): "${component.content}"

${variationInstruction}

Requirements:
1. Use completely different words and phrasing - NO OVERLAP with current version
2. Try a different angle or creative approach
3. Make it distinctly different from the current version
4. Maintain ${tone} tone
5. Keep similar length (~${component.content.length} characters)
6. Ensure it's unique compared to similar components above
7. Regeneration attempt: ${timestamp}
8. Random seed: ${randomSeed}

OUTPUT: Generate ONLY the new "${component.label}" text (not the entire email). 
Make it UNIQUE and DIFFERENT from "${component.content}".
This is attempt #${iteration} - be creative and original!`
      
      // Use even higher temperature for short components (CTAs)
      const tempBoost = isShortComponent ? 0.5 : 0.3
      const regenerateTemp = Math.min(temperature + tempBoost, 1.0)
      
      // Generate 3 candidates and pick the most different one
      // Use Flash model for CTAs (faster, cheaper, same quality for short text)
      // Use Few-Shot examples for brand consistency
      // NOTE: Don't send image for regeneration - not needed and causes issues with Flash
      const result = await generateContent({
        text: enhancedBrief,
        count: 3, // Generate 3 options to increase variety
        tone: tone,
        content_type: "newsletter",
        structure: [{ component: componentType, count: 1 }],
        image_url: undefined, // No image needed for single component regeneration
        temperature: regenerateTemp,
        use_flash: isShortComponent, // Use Flash for CTAs and other short components
        use_few_shot: true // Use Few-Shot examples for regeneration only
      })
      
      // Debug: Log the full result
      console.log("📡 API RESPONSE:", {
        success: result.success,
        componentKey: component.key,
        componentType: componentType,
        rawData: result.data,
        variations: result.data?.variations
      })

      if (result.success && result.data) {
        // Normalize function to compare content (remove spaces, lowercase, punctuation)
        const normalize = (str: string) => 
          str.trim().toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ')
        
        const currentNormalized = normalize(component.content)
        
        // FIXED: Use componentType as key (e.g., "cta"), not component.key (e.g., "cta_2")
        // The API returns {"cta": "..."}, not {"cta_2": "..."}
        const lookupKey = componentType
        
        // Get all variations and check each one
        const allVariations = result.data.variations.map(v => ({
          original: v[lookupKey] || '',
          normalized: normalize(v[lookupKey] || '')
        }))
        
        // Find truly different candidates (not just spacing/case differences)
        const differentCandidates = allVariations.filter(v => 
          v.normalized !== currentNormalized && v.original.trim() !== ''
        )
        
        // Log for debugging
        console.log("🔍 REGENERATION DEBUG:", {
          current: component.content,
          currentNormalized,
          allVariations: allVariations.map(v => v.original),
          differentCount: differentCandidates.length
        })
        
        // Check if ALL variations are essentially the same (ignoring minor differences)
        if (differentCandidates.length === 0) {
          // FORCE ERROR: AI generated the same content (even with minor variations)
          toast.error(`❌ CTA invariato! L'AI ha generato "${component.content}" 3 volte. Problema di caching AI. Riprova o usa "Regenerate All".`)
          console.error("🚨 REGENERATION FAILED: All 3 variations are identical", {
            current: component.content,
            generated: allVariations.map(v => v.original)
          })
          return // Don't update the component
        }
        
        // Use first truly different candidate
        let newContent = differentCandidates[0].original
        
        // Normalize CTAs to UPPERCASE for brand consistency
        const isCTA = component.key.toLowerCase().includes('cta')
        if (isCTA) {
          newContent = newContent.toUpperCase()
        }
        
        if (newContent) {
          // Update components with new content
          const updatedComponents = components.map((comp, i) =>
            i === index ? { ...comp, content: newContent } : comp
          )
          
          setComponents(updatedComponents)
          
          toast.success(`✅ Rigenerato! (${differentCandidates.length}/3 varianti diverse trovate)`)
          
          // If this component had translations, automatically regenerate them
          const hadTranslations = translations[component.key] && Object.keys(translations[component.key]).length > 0
          
          if (hadTranslations && targetLanguages.length > 0) {
            toast.info("🔄 Rigenerando traduzioni per questa componente...")
            setIsTranslating(true) // Set translating state for visual feedback
            
            try {
              // Regenerate translations for this specific component
              const result = await batchTranslate(
                [{ key: component.key, content: newContent }],
                targetLanguages
              )
              
              if (result.success && result.data) {
                // Update translations for this component only
                const updatedTranslations = {
                  ...translations,
                  ...result.data
                }
                setTranslations(updatedTranslations)
                
                // Auto-save with updated translations
                await saveComponentsToDatabase(updatedComponents, updatedTranslations)
                
                toast.success(`✅ Traduzioni rigenerate per ${targetLanguages.length} lingua/e`)
              } else {
                toast.error("❌ Errore rigenerando le traduzioni")
              }
            } finally {
              setIsTranslating(false) // Reset translating state
            }
          } else {
            // Just save without translations
            await saveComponentsToDatabase(updatedComponents, translations)
          }
        }
      } else {
        toast.error("Failed to regenerate component")
      }
    } catch (error) {
      console.error("Error regenerating component:", error)
      toast.error("Failed to regenerate component")
    } finally {
      setRegeneratingIndex(null)
    }
  }

  const copyHandlebar = async (component: GeneratedComponent) => {
    // If no translations, generate handlebar with only English
    const componentTranslations = translations[component.key] || {}

    const result = await generateHandlebar({
      component_key: component.key,
      translations: componentTranslations,
      english_fallback: component.content
    })

    if (result.success && result.data) {
      try {
        await navigator.clipboard.writeText(result.data.handlebar_template)
        const langCount = Object.keys(componentTranslations).length
        if (langCount === 0) {
          toast.success("Handlebar template copied (English only)")
        } else {
          toast.success(`Handlebar template copied (${langCount + 1} languages)`)
        }
      } catch (clipboardError) {
        // Fallback for when clipboard API fails (document not focused, permissions, etc.)
        console.error("Clipboard error:", clipboardError)
        
        // Try legacy execCommand as fallback
        try {
          const textArea = document.createElement("textarea")
          textArea.value = result.data.handlebar_template
          textArea.style.position = "fixed"
          textArea.style.left = "-999999px"
          document.body.appendChild(textArea)
          textArea.select()
          document.execCommand("copy")
          document.body.removeChild(textArea)
          
          const langCount = Object.keys(componentTranslations).length
          if (langCount === 0) {
            toast.success("Handlebar template copied (English only)")
          } else {
            toast.success(`Handlebar template copied (${langCount + 1} languages)`)
          }
        } catch (fallbackError) {
          console.error("Fallback copy failed:", fallbackError)
          toast.error("Failed to copy to clipboard. Please try again.")
        }
      }
    } else {
      toast.error("Failed to generate handlebar")
    }
  }

  const toggleEdit = (index: number) => {
    setComponents((prev) =>
      prev.map((comp, i) =>
        i === index ? { ...comp, editing: !comp.editing } : comp
      )
    )
  }

  const updateContent = async (index: number, newContent: string) => {
    const updatedComponents = components.map((comp, i) =>
      i === index ? { ...comp, content: newContent } : comp
    )
    setComponents(updatedComponents)
  }

  const saveAndRetranslate = async (index: number) => {
    const component = components[index]
    
    // Close editing mode
    setComponents((prev) =>
      prev.map((comp, i) =>
        i === index ? { ...comp, editing: false } : comp
      )
    )
    
    // Check if this component had translations
    const hadTranslations = translations[component.key] && Object.keys(translations[component.key]).length > 0
    
    // Save to database
    await saveComponentsToDatabase(components, translations)
    toast.success("✅ Saved!")
    
    // If had translations and languages are selected, retranslate
    if (hadTranslations && targetLanguages.length > 0) {
      toast.info("🔄 Retranslating edited content...")
      setIsTranslating(true)
      
      try {
        const result = await batchTranslate(
          [{ key: component.key, content: component.content }],
          targetLanguages
        )
        
        if (result.success && result.data) {
          const updatedTranslations = {
            ...translations,
            ...result.data
          }
          setTranslations(updatedTranslations)
          
          await saveComponentsToDatabase(components, updatedTranslations)
          toast.success(`✅ Retranslated to ${targetLanguages.length} language(s)`)
        } else {
          toast.error("❌ Error retranslating")
        }
      } finally {
        setIsTranslating(false)
      }
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("Copied to clipboard!")
  }

  const handleTranslate = async () => {
    if (components.length === 0) {
      toast.error("Please generate content first")
      return
    }

    if (targetLanguages.length === 0) {
      toast.error("No target languages selected")
      return
    }

    setIsTranslating(true)
    try {
      const textsToTranslate = components.map((comp) => ({
        key: comp.key,
        content: comp.content
      }))

      const result = await batchTranslate(textsToTranslate, targetLanguages)

      if (result.success && result.data) {
        setTranslations(result.data)
        toast.success(`Translated to ${targetLanguages.length} languages!`)
        
        // Auto-save to database with translations
        await saveComponentsToDatabase(components, result.data)
        
        // Add persistent notification for team handoff
        addNotification({
          type: "success",
          title: "Translation Completed",
          message: `Content translated to ${targetLanguages.length} language(s) by ${userName}. Translation team can now review. Ready for Airship export.`
        })
      } else {
        throw new Error(result.error || "Failed to translate")
      }
    } catch (error) {
      console.error("Error translating:", error)
      toast.error("Failed to translate content. Please try again.")
    } finally {
      setIsTranslating(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>AI Content Generation</CardTitle>
            <CardDescription>
              Generate email content based on your brief and structure
            </CardDescription>
          </div>
          {isSaving && (
            <Badge variant="secondary" className="ml-auto">
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              Saving...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Temperature Control */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="temperature">Creativity Level (Temperature)</Label>
            <span className="text-sm text-muted-foreground">{temperature.toFixed(1)}</span>
          </div>
          <Slider
            id="temperature"
            min={0}
            max={1}
            step={0.1}
            value={[temperature]}
            onValueChange={(values: number[]) => setTemperature(values[0])}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Lower = more consistent, Higher = more creative
          </p>
        </div>

        {/* Generate/Regenerate Button */}
        <Button
          onClick={components.length > 0 ? handleRegenerateAll : handleGenerate}
          disabled={isGenerating || !brief.trim()}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              {components.length > 0 ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Regenerate All Content
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Email Content
                </>
              )}
            </>
          )}
        </Button>

        {/* Translation Section - Only show after content generation */}
        {components.length > 0 && (
          <div className="space-y-3 pt-4 border-t">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Translation Languages</Label>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => {
                  const isSelected = targetLanguages.includes(lang.value)
                  return (
                    <Badge
                      key={lang.value}
                      variant={isSelected ? "default" : "outline"}
                      className="cursor-pointer hover:bg-primary/80"
                      onClick={() => {
                        if (onLanguagesChange) {
                          if (isSelected) {
                            onLanguagesChange(targetLanguages.filter((l) => l !== lang.value))
                          } else {
                            onLanguagesChange([...targetLanguages, lang.value])
                          }
                        }
                      }}
                    >
                      {lang.label}
                    </Badge>
                  )
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                Click to add or remove languages for translation
              </p>
            </div>

            {targetLanguages.length > 0 && (
              <Button
                variant="default"
                size="default"
                onClick={handleTranslate}
                disabled={isTranslating}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isTranslating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Translating to {targetLanguages.length} language(s)...
                  </>
                ) : (
                  <>
                    <Languages className="mr-2 h-4 w-4" />
                    Translate to {targetLanguages.length} language(s)
                  </>
                )}
              </Button>
            )}
          </div>
        )}

        {/* Generated Components */}
        {components.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Generated Content</h3>
              <Badge variant="secondary">{components.length} components</Badge>
            </div>

            {components.map((component, index) => (
              <div
                key={component.key}
                className="rounded-lg border bg-card p-4 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{component.label}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {component.content.length} chars
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRegenerateSingle(index)}
                      disabled={regeneratingIndex === index}
                      title="Regenerate this component"
                    >
                      {regeneratingIndex === index ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <RefreshCw className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleEdit(index)}
                      title="Edit content"
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(component.content)}
                      title="Copy to clipboard"
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyHandlebar(component)}
                      title="Copy handlebar template"
                    >
                      <FileCode className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>

                {component.editing ? (
                  <div className="space-y-2">
                    <Textarea
                      value={component.content}
                      onChange={(e) => updateContent(index, e.target.value)}
                      rows={4}
                      className="font-mono text-sm"
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => saveAndRetranslate(index)}
                        disabled={isTranslating}
                        className="gap-2"
                      >
                        {isTranslating ? (
                          <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Check className="h-3.5 w-3.5" />
                            Save & Retranslate
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggleEdit(index)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">
                    {component.content}
                  </p>
                )}

                {/* Translations */}
                {translations[component.key] &&
                  Object.keys(translations[component.key]).length > 0 && (
                    <div className="mt-4 space-y-3 pt-4 border-t">
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-medium text-muted-foreground uppercase">
                          Translations
                        </p>
                        {isTranslating && (
                          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                        )}
                      </div>
                      {Object.entries(translations[component.key]).map(
                        ([lang, translatedText]) => (
                          <div
                            key={lang}
                            className={`rounded-md bg-muted/50 p-3 space-y-1 transition-opacity ${
                              isTranslating ? 'opacity-50' : 'opacity-100'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <Badge variant="secondary" className="uppercase">
                                {lang}
                              </Badge>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyToClipboard(translatedText)}
                                disabled={isTranslating}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </div>
                            <p className="text-sm">{translatedText}</p>
                          </div>
                        )
                      )}
                    </div>
                  )}
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {components.length === 0 && !isGenerating && (
          <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
            <Sparkles className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">Click "Generate Email Content" to create your email</p>
            <p className="text-xs mt-2">
              Make sure you have a brief and structure defined
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

