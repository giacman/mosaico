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
import { useNotifications } from "./notifications-provider"

interface ContentGeneratorProps {
  projectId: number
  brief: string
  tone: string
  structure: Array<{ component: string; count: number }>
  targetLanguages: string[]
  imageUrls?: string[]
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
  imageUrls = []
}: ContentGeneratorProps) {
  const { addNotification } = useNotifications()
  const [isGenerating, setIsGenerating] = useState(false)
  const [components, setComponents] = useState<GeneratedComponent[]>([])
  const [isTranslating, setIsTranslating] = useState(false)
  const [translations, setTranslations] = useState<Record<string, Record<string, string>>>({})
  const [temperature, setTemperature] = useState(0.7)
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null)

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
      const result = await generateContent({
        text: brief,
        count: 1, // Generate 1 variation
        tone: tone,
        content_type: "newsletter",
        structure: structure,
        image_url: imageUrls[0], // Use first image if available
        temperature: temperature
      })

      if (result.success && result.data) {
        // Convert first (and only) variation to components
        const firstVariation = result.data.variations[0]
        const generatedComponents: GeneratedComponent[] = Object.entries(firstVariation).map(
          ([key, content]) => ({
            key,
            label: formatLabel(key),
            content: content as string,
            editing: false
          })
        )
        
        setComponents(generatedComponents)
        toast.success("Content generated successfully!")
        
        // Add persistent notification for team handoff
        addNotification({
          type: "success",
          title: "Content Generated",
          message: `AI has generated ${generatedComponents.length} components. Content team can now review for quality.`
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

  const formatLabel = (key: string): string => {
    return key
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  const handleRegenerateAll = async () => {
    await handleGenerate()
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
      const enhancedBrief = `${brief}

FULL EMAIL CONTEXT (for reference):
${existingContext}

CRITICAL INSTRUCTION - You MUST regenerate ONLY the "${component.label}" component:
Current version (DO NOT REPEAT): "${component.content}"

Requirements:
1. Use completely different words and phrasing
2. Try a different angle or creative approach
3. Make it distinctly different from the current version
4. Maintain ${tone} tone
5. Keep similar length (~${component.content.length} characters)
6. Ensure it's unique compared to similar components above
7. Regeneration attempt: ${timestamp}

Variation seed: ${randomSeed}

OUTPUT: Generate ONLY the new "${component.label}" text (not the entire email). Make it UNIQUE and DIFFERENT from "${component.content}".`
      
      // Use significantly higher temperature for regeneration to increase variety
      const regenerateTemp = Math.min(temperature + 0.3, 1.0)
      
      const result = await generateContent({
        text: enhancedBrief,
        count: 1,
        tone: tone,
        content_type: "newsletter",
        structure: [{ component: componentType, count: 1 }],
        image_url: imageUrls[0],
        temperature: regenerateTemp
      })

      if (result.success && result.data) {
        const newContent = result.data.variations[0][component.key]
        if (newContent) {
          setComponents((prev) =>
            prev.map((comp, i) =>
              i === index ? { ...comp, content: newContent } : comp
            )
          )
          toast.success(`Regenerated ${component.label}`)
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
    if (!translations[component.key] || Object.keys(translations[component.key]).length === 0) {
      toast.error("Please translate this component first")
      return
    }

    const result = await generateHandlebar({
      component_key: component.key,
      translations: translations[component.key],
      english_fallback: component.content
    })

    if (result.success && result.data) {
      navigator.clipboard.writeText(result.data.handlebar_template)
      toast.success("Handlebar template copied!")
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

  const updateContent = (index: number, newContent: string) => {
    setComponents((prev) =>
      prev.map((comp, i) =>
        i === index ? { ...comp, content: newContent } : comp
      )
    )
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
        
        // Add persistent notification for team handoff
        addNotification({
          type: "success",
          title: "Translation Completed",
          message: `Content translated to ${targetLanguages.length} language(s). Translation team can now review. Ready for Airship export.`
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
        <CardTitle>AI Content Generation</CardTitle>
        <CardDescription>
          Generate email content based on your brief and structure
        </CardDescription>
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

        {/* Generate Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !brief.trim()}
            className="flex-1"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Email Content
              </>
            )}
          </Button>
          
          {components.length > 0 && (
            <Button
              onClick={handleRegenerateAll}
              disabled={isGenerating}
              variant="outline"
              size="lg"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate All
            </Button>
          )}
        </div>

        {/* Translate Button */}
        {components.length > 0 && targetLanguages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleTranslate}
            disabled={isTranslating}
            className="w-full"
          >
            {isTranslating ? (
              <>
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                Translating...
              </>
            ) : (
              <>
                <Languages className="mr-2 h-3.5 w-3.5" />
                Translate to {targetLanguages.length} language(s)
              </>
            )}
          </Button>
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
                    {translations[component.key] && Object.keys(translations[component.key]).length > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyHandlebar(component)}
                        title="Copy handlebar template"
                      >
                        <FileCode className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>

                {component.editing ? (
                  <Textarea
                    value={component.content}
                    onChange={(e) => updateContent(index, e.target.value)}
                    rows={4}
                    className="font-mono text-sm"
                  />
                ) : (
                  <p className="text-sm whitespace-pre-wrap">
                    {component.content}
                  </p>
                )}

                {/* Translations */}
                {translations[component.key] &&
                  Object.keys(translations[component.key]).length > 0 && (
                    <div className="mt-4 space-y-3 pt-4 border-t">
                      <p className="text-xs font-medium text-muted-foreground uppercase">
                        Translations
                      </p>
                      {Object.entries(translations[component.key]).map(
                        ([lang, translatedText]) => (
                          <div
                            key={lang}
                            className="rounded-md bg-muted/50 p-3 space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <Badge variant="secondary" className="uppercase">
                                {lang}
                              </Badge>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyToClipboard(translatedText)}
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

