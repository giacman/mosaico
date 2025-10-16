"use client"

import { useState } from "react"
import { Sparkles, Loader2, Copy, Check, Edit2, Languages } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { generateContent } from "@/actions/generate"
import { batchTranslate } from "@/actions/translate"

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
  const [isGenerating, setIsGenerating] = useState(false)
  const [components, setComponents] = useState<GeneratedComponent[]>([])
  const [selectedVariation, setSelectedVariation] = useState(0)
  const [allVariations, setAllVariations] = useState<any[]>([])
  const [isTranslating, setIsTranslating] = useState(false)
  const [translations, setTranslations] = useState<Record<string, Record<string, string>>>({})

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
        count: 3, // Generate 3 variations
        tone: tone,
        content_type: "newsletter",
        structure: structure,
        image_url: imageUrls[0] // Use first image if available
      })

      if (result.success && result.data) {
        setAllVariations(result.data.variations)
        setSelectedVariation(0)
        
        // Convert first variation to components
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
        toast.success(`Generated ${result.data.variations.length} variations!`)
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

  const handleVariationChange = (index: number) => {
    setSelectedVariation(index)
    const variation = allVariations[index]
    const generatedComponents: GeneratedComponent[] = Object.entries(variation).map(
      ([key, content]) => ({
        key,
        label: formatLabel(key),
        content: content as string,
        editing: false
      })
    )
    setComponents(generatedComponents)
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
      <CardContent className="space-y-4">
        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          disabled={isGenerating || !brief.trim()}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating content...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Email Content
            </>
          )}
        </Button>

        {/* Variation Selector & Translate Button */}
        {allVariations.length > 0 && (
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Variation:</span>
              <div className="flex gap-2">
                {allVariations.map((_, index) => (
                  <Button
                    key={index}
                    variant={selectedVariation === index ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleVariationChange(index)}
                  >
                    {index + 1}
                  </Button>
                ))}
              </div>
            </div>
            
            {targetLanguages.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleTranslate}
                disabled={isTranslating}
              >
                {isTranslating ? (
                  <>
                    <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                    Translating...
                  </>
                ) : (
                  <>
                    <Languages className="mr-2 h-3.5 w-3.5" />
                    Translate ({targetLanguages.length} langs)
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
                      onClick={() => toggleEdit(index)}
                    >
                      <Edit2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(component.content)}
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
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

