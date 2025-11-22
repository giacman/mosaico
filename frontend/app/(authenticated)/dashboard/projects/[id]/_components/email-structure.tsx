"use client"

import { useState, useEffect } from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Sparkles, Loader2, CheckCircle2 } from "lucide-react"
import { type Project } from "@/actions/projects"
import { RenderedComponent } from "../../../_components/rendered-component" // Import the new component
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { generate } from "@/actions/generate"
import { toast } from "sonner"
import { Separator } from "@/components/ui/separator"
import { getLabelColor } from "../../../_components/create-project-dialog"
import { SectionBuilder } from "./section-builder"
import { PromptAssistantDialog } from "../../../_components/prompt-assistant-dialog"
import { batchTranslate } from "@/actions/translate"
import { saveGeneratedComponents } from "@/actions/components"
import { useNotifications } from "../../../_components/notifications-provider"

const LANGUAGES = [
  { value: "it", label: "Italian", flag: "🇮🇹" },
  { value: "de", label: "German", flag: "🇩🇪" },
  { value: "fr", label: "French", flag: "🇫🇷" },
  { value: "es", label: "Spanish", flag: "🇪🇸" },
  { value: "pt", label: "Portuguese", flag: "🇵🇹" },
  { value: "ru", label: "Russian", flag: "🇷🇺" },
  { value: "zh", label: "Chinese", flag: "🇨🇳" },
  { value: "ja", label: "Japanese", flag: "🇯🇵" },
  { value: "ar", label: "Arabic", flag: "🇸🇦" },
  { value: "nl", label: "Dutch", flag: "🇳🇱" }
]

interface UploadedImage {
  id: string
  url: string
  filename: string
  uploading?: boolean
}

interface EmailStructureProps {
  project: Project
  onProjectChange: (field: keyof Project, value: any) => void
  onStructureChange: (
    structure: Array<{
      key: string
      name: string
      components: Array<string>
    }>
  ) => void
  onImagesChange: (images: UploadedImage[]) => void
  userName: string
}

export function EmailStructure({
  project,
  onProjectChange,
  onStructureChange,
  onImagesChange,
  userName
}: EmailStructureProps) {
  const [temperature, setTemperature] = useState(0.5)
  const [tone, setTone] = useState(project.tone ?? "professional")


  const [isGenerating, setIsGenerating] = useState(false)
  const [sections, setSections] = useState(() => {
    const initialStructure = Array.isArray(project.structure)
      ? (project.structure as Array<any>)
      : []

    if (
      initialStructure.length > 0 &&
      initialStructure[0] &&
      initialStructure[0].components
    ) {
      return initialStructure
    } else {
      // This is the old structure, let's convert it
      const components = initialStructure
        .flatMap((it: any) => {
          const comp = it.component as string
          const count = Number(it.count ?? 1) || 1
          if (comp === "subject" || comp === "pre_header") return []
          return Array.from({ length: count }, () => comp)
        })
        .filter(Boolean)

      return [{ key: "main", name: "Main Section", components }]
    }
  })
  const [images, setImages] = useState<UploadedImage[]>([])
  const [showPromptAssistant, setShowPromptAssistant] = useState(false)
  const hasComponents = Array.isArray((project as any).components) && ((project as any).components.length > 0)
  const [isTranslating, setIsTranslating] = useState(false)
  const [translatedLanguages, setTranslatedLanguages] = useState<Set<string>>(new Set())
  const [viewLang, setViewLang] = useState<string>("en")
  const { addNotification } = useNotifications()

  // Check which languages already have translations on mount/update
  useEffect(() => {
    if (hasComponents && project.components) {
      const langsWithTranslations = new Set<string>()
      project.components.forEach((comp: any) => {
        if (comp.translations && typeof comp.translations === 'object') {
          Object.keys(comp.translations).forEach(lang => {
            if (comp.translations[lang]) langsWithTranslations.add(lang.toLowerCase())
          })
        }
      })
      setTranslatedLanguages(langsWithTranslations)
    }
  }, [hasComponents, project.components])

  // Normalize translations into a plain { lang: text } map and filter to current target languages
  const normalizeTranslationsMap = (input: any): Record<string, string> => {
    if (!input) return {}
    if (typeof input === "object" && !Array.isArray(input)) {
      const out: Record<string, string> = {}
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
      return out
    }
    if (Array.isArray(input)) {
      const out: Record<string, string> = {}
      input.forEach((it) => {
        if (it && typeof it === "object") {
          const lang = (it as any).language_code || (it as any).lang || (it as any).code
          const text = (it as any).translated_content || (it as any).content || (it as any).text
          if (lang && text) out[String(lang).toLowerCase()] = String(text)
        }
      })
      return out
    }
    return {}
  }

  const normalizeComponentList = (list: any[]): any[] => {
    const allowed = new Set((project.target_languages || []).map((l) => String(l).toLowerCase()))
    return (list || []).map((c: any) => {
      const raw = normalizeTranslationsMap(c.translations)
      const filtered = Object.fromEntries(Object.entries(raw).filter(([k]) => allowed.has(String(k).toLowerCase())))
      // Remove section_key and section_order as backend doesn't accept them in save requests
      const { section_key, section_order, image, ...rest } = c
      // Ensure generated_content is never null (backend requires string)
      return { 
        ...rest, 
        generated_content: rest.generated_content ?? "",
        translations: filtered 
      }
    })
  }

  const toggleLabel = (label: string) => {
    const currentLabels = project.labels || []
    const newLabels = currentLabels.includes(label)
      ? currentLabels.filter((l) => l !== label)
      : [...currentLabels, label]
    onProjectChange("labels", newLabels)
  }

  const handleGenerate = async () => {
    if (!project.brief_text?.trim()) {
      toast.error("Please enter a creative brief first")
      return
    }

    setIsGenerating(true)
    try {
      const legacyStructure: Array<{ component: string; count: number }> =
        (() => {
          const counts: Record<string, number> = { title: 0, body: 0, cta: 0 }
          for (const sec of sections) {
            for (const c of sec.components || []) {
              if (c === "title" || c === "body" || c === "cta")
                counts[c] = (counts[c] || 0) + 1
            }
          }
          const result: Array<{ component: any; count: number }> = [
            { component: "subject", count: 1 },
            { component: "pre_header", count: 1 }
          ]
          if (counts.title > 0)
            result.push({ component: "title", count: counts.title })
          if (counts.body > 0)
            result.push({ component: "body", count: counts.body })
          if (counts.cta > 0)
            result.push({ component: "cta", count: counts.cta })
          return result
        })()

      const result = await generate({
        project_id: project.id,
        text: project.brief_text,
        count: 1,
        tone: tone,
        content_type: "newsletter",
        structure: legacyStructure,
        temperature: temperature,
        image_url: images[0]?.url
      })

      if (result.success && result.data) {
        // Clear translation status since we have new content
        setTranslatedLanguages(new Set())
        
        toast.success("Content generated successfully!")
        addNotification({
          type: "success",
          title: "Generation Completed",
          message: `Generated ${Object.keys(result.data.variations?.[0] || {}).length} components`
        })
        
        // Extract the components from the first variation with stable per-type indices
        const variation = result.data.variations[0]
        const typeCounters: Record<string, number> = { subject: 0, pre_header: 0, title: 0, body: 0, cta: 0 }
        const newTextComponents = Object.entries(variation).flatMap(([key, content]) => {
          const m = key.match(/^(subject|pre_header|title|body|cta)(?:_(\d+))?$/)
          if (!m) return []
          const type = m[1]
          const parsedIdx = m[2] ? parseInt(m[2], 10) : undefined
          const index = parsedIdx ?? ((typeCounters[type] || 0) + 1)
          typeCounters[type] = Math.max(typeCounters[type] || 0, index)
          const text = String(content ?? "")
          return [{
            component_type: type,
            component_index: index,
            generated_content: type === "cta" ? text.toUpperCase() : text,
            translations: {} as Record<string, string>
          }]
        })

        // Preserve existing image components
        const existingImages = (project.components || []).filter((c: any) => c.component_type === "image")
        const allComponents = [...newTextComponents, ...existingImages]

        // If current sections are empty, create a default Main Section from the requested counts
        const hasAnyComponents = sections.some(sec => (sec.components || []).length > 0)
        if (!hasAnyComponents) {
          const defaultComponents: string[] = []
          legacyStructure.forEach(it => {
            if (it.component === "title" || it.component === "body" || it.component === "cta") {
              for (let i = 0; i < (it.count || 0); i++) defaultComponents.push(it.component)
            }
          })
          const newSections = [{ key: "main", name: "Main Section", components: defaultComponents }]
          setSections(newSections)
          onProjectChange("structure", newSections as any)
        }

        onProjectChange("components", allComponents)
      } else {
        toast.error(result.error || "Failed to generate content")
      }
    } catch (error) {
      toast.error("An unexpected error occurred.")
      console.error(error)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* TOP SECTION: Project Details */}
      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
          <CardDescription>
            Basic information about your email campaign
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Project Name */}
          <div className="space-y-2">
            <Label htmlFor="project-name">Project Name</Label>
            <Input
              id="project-name"
              value={project.name}
              onChange={(e) => onProjectChange("name", e.target.value)}
              placeholder="e.g., Spring Collection Launch"
            />
          </div>

          {/* Project Labels */}
          <div className="space-y-2">
            <Label>Project Labels</Label>
            <div className="flex flex-wrap gap-2">
              {[
                "promo",
                "category",
                "design",
                "october 2025",
                "november 2025",
                "december 2025"
              ].map((label) => {
                const isSelected = project.labels?.includes(label) || false
                const colors = getLabelColor(label)
                return (
                  <Badge
                    key={label}
                    variant={isSelected ? "default" : "outline"}
                    className={`cursor-pointer hover:opacity-80 transition-opacity ${
                      isSelected
                        ? `${colors.bg} ${colors.text} ${colors.border} border`
                        : ""
                    }`}
                    onClick={() => toggleLabel(label)}
                  >
                    {label}
                  </Badge>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* BOTTOM SECTION: Two Columns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* LEFT COLUMN: Content Generation */}
        <Card>
          <CardHeader>
            <CardTitle>Content Generation</CardTitle>
            <CardDescription>
              Generate email content with AI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">

            {/* Creative Brief */}
            <div className="space-y-2">
              <Label htmlFor="project-brief">Creative Brief</Label>
              <Textarea
                id="project-brief"
                value={project.brief_text ?? ""}
                onChange={(e) =>
                  onProjectChange("brief_text", e.target.value || null)
                }
                placeholder="Describe the theme, target audience, key messages..."
                rows={4}
              />
            </div>

            {/* Tone of Voice and Creativity Level - Side by Side */}
            <div className="grid grid-cols-5 gap-4">
              {/* Tone of Voice */}
              <div className="space-y-2 col-span-2">
                <Label>Tone of Voice</Label>
                <Select value={tone} onValueChange={setTone}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select tone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="enthusiastic">Enthusiastic</SelectItem>
                    <SelectItem value="elegant">Elegant</SelectItem>
                    <SelectItem value="direct">Direct</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Creativity Level */}
              <div className="space-y-2 col-span-3">
                <Label>Creativity Level</Label>
                <div className="pt-2">
                  <Slider
                    value={[temperature]}
                    onValueChange={(value) => setTemperature(value[0])}
                    min={0}
                    max={1}
                    step={0.1}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Conservative</span>
                    <span>Balanced</span>
                    <span>Creative</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Optimize Prompt Button */}
            <Button
              type="button"
              variant="outline"
              className="w-full gap-2"
              onClick={() => setShowPromptAssistant(true)}
              disabled={!project.brief_text?.trim()}
            >
              <Sparkles className="h-4 w-4" />
              Optimize Prompt
            </Button>

            {/* Generate / Regenerate Button */}
            <Button
              size="lg"
              className="w-full"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              {hasComponents ? "Regenerate All Content" : "Generate Content"}
            </Button>
          </CardContent>
        </Card>

        {/* RIGHT COLUMN: Translation & Languages */}
        <Card>
          <CardHeader>
            <CardTitle>Translation & Languages</CardTitle>
            <CardDescription>
              Translate your content to multiple languages
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Translation Languages */}
            <div className="space-y-2">
              <Label className="text-sm">Translation Languages</Label>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => {
                  const selected = (project.target_languages || []).includes(lang.value)
                  return (
                    <Badge
                      key={lang.value}
                      variant={selected ? "default" : "outline"}
                      className="cursor-pointer gap-1.5"
                      onClick={() => {
                        const curr = project.target_languages || []
                        const next = selected ? curr.filter((l) => l !== lang.value) : [...curr, lang.value]
                        onProjectChange("target_languages", next as any)
                      }}
                    >
                      <span className="text-base leading-none">{lang.flag}</span>
                      {lang.label}
                    </Badge>
                  )
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                Select 1+ languages to enable translation
              </p>
            </div>

            {/* Translate Selected Languages Button */}
            {((project.target_languages || []).length > 0) && hasComponents && (
              <Button
                variant="default"
                className="w-full"
                disabled={isTranslating}
                onClick={async () => {
                  try {
                    setIsTranslating(true)
                    const texts = (project.components || []).map((c: any) => ({ key: `${c.component_type}${c.component_index ? `_${c.component_index}`: ""}`, content: c.generated_content || "" }))
                    if (texts.length === 0) { toast.error("Generate content first"); return }
                    const langs = project.target_languages || []
                    const res = await batchTranslate(texts, langs)
                    if (res.success && res.data) {
                      const merged = (project.components || []).map((c: any) => {
                        const key = `${c.component_type}${c.component_index ? `_${c.component_index}`: ""}`
                        const rawT = (res.data as any)[key] || {}
                        const t = c.component_type === "cta"
                          ? Object.fromEntries(Object.entries(rawT).map(([k,v]) => [k, String(v || "").toUpperCase()]))
                          : rawT
                        const curr = normalizeTranslationsMap(c.translations)
                        return { ...c, translations: { ...curr, ...t } }
                      })
                      const normalized = normalizeComponentList(merged as any)
                      onProjectChange("components", normalized as any)
                      await saveGeneratedComponents(project.id, normalized as any)
                      
                      // Mark languages as successfully translated
                      setTranslatedLanguages(new Set(langs))
                      
                      toast.success(`Translated to ${langs.length} language(s)`)  
                      addNotification({
                        type: "success",
                        title: "Translation Completed",
                        message: `Translated ${texts.length} component(s) to ${langs.length} language(s)`
                      })
                    } else {
                      toast.error(res.error || "Translation failed")
                    }
                  } catch (e) { toast.error("Translation error") }
                  finally { setIsTranslating(false) }
                }}
              >
                {isTranslating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Translating...
                  </>
                ) : (
                  "Translate Selected Languages"
                )}
              </Button>
            )}

            <Separator />

            {/* View Language Tabs */}
            <div className="space-y-2">
              <Label className="text-sm">View Language</Label>
              <div className="flex flex-wrap gap-2">
                {[{value:"en",label:"English",flag:"🇬🇧"}, ...LANGUAGES.filter(l => (project.target_languages||[]).includes(l.value))].map((l) => {
                  const isTranslated = l.value === "en" || translatedLanguages.has(l.value)
                  const showSpinner = isTranslating && l.value !== "en"
                  
                  return (
                    <Badge
                      key={l.value}
                      variant={viewLang === l.value ? "default" : "outline"}
                      className="cursor-pointer gap-1.5"
                      onClick={() => setViewLang(l.value)}
                    >
                      <span className="text-base leading-none">{l.flag}</span>
                      {l.label}
                      {showSpinner && (
                        <Loader2 className="h-3 w-3 animate-spin ml-1" />
                      )}
                      {isTranslated && !showSpinner && l.value !== "en" && (
                        <CheckCircle2 className="h-3 w-3 ml-1 text-green-500" />
                      )}
                    </Badge>
                  )
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sections Builder (Add Sections/Components, Drag&Drop, Image upload) */}
      <SectionBuilder
        projectId={project.id}
        value={sections as any}
        onChange={(next) => {
          setSections(next as any)
          onProjectChange("structure", next as any)
        }}
        onImagesChange={(imgs) => setImages(imgs)}
        components={(project.components as any) || []}
        projectImages={(project.images as any) || []}
        brief={project.brief_text || ""}
        tone={tone}
        currentLanguage={viewLang}
        targetLanguages={(project.target_languages as any) || []}
        onUpdateComponents={async (list) => {
          const normalized = normalizeComponentList(list as any)
          
          // Optimistically update the UI for responsiveness
          onProjectChange("components", normalized as any)
          
          // Update translation status based on new components
          const langsWithTranslations = new Set<string>()
          normalized.forEach((comp: any) => {
            if (comp.translations && typeof comp.translations === 'object') {
              Object.keys(comp.translations).forEach(lang => {
                if (comp.translations[lang]) langsWithTranslations.add(lang.toLowerCase())
              })
            }
          })
          setTranslatedLanguages(langsWithTranslations)
          
          // Save and get the definitive state from the backend
          const result = await saveGeneratedComponents(project.id, normalized as any)
          
          if (result.success && result.components) {
            // Backend returns translations as array, convert to object format
            const normalizedFromBackend = (result.components || []).map((comp: any) => {
              if (Array.isArray(comp.translations)) {
                // Convert array format to object format
                const translationsObj: Record<string, string> = {}
                comp.translations.forEach((t: any) => {
                  if (t.language_code && t.translated_content) {
                    translationsObj[t.language_code] = t.translated_content
                  }
                })
                return { ...comp, translations: translationsObj }
              }
              return comp
            })
            
            // Sync the UI with the backend's source of truth
            onProjectChange("components", normalizedFromBackend as any)
            // Also update images if the backend returned them
            if (result.images) {
              onProjectChange("images", result.images as any)
            }
          }
        }}
        onUpdateComponent={(type, index, content) => {
          const list: any[] = [...((project.components as any) || [])]
          const idx = list.findIndex((c: any) => c.component_type === type && (c.component_index || 1) === index)
          const finalContent = type === "cta" ? (content || "").toUpperCase() : content
          if (idx >= 0) list[idx] = { ...list[idx], generated_content: finalContent }
          else list.push({ component_type: type, component_index: index, generated_content: finalContent, translations: {} })
          const normalized = normalizeComponentList(list as any)
          onProjectChange("components", normalized as any)
        }}
      />

      {/* Prompt Assistant Dialog */}
      <PromptAssistantDialog
        open={showPromptAssistant}
        onOpenChange={setShowPromptAssistant}
        originalBrief={project.brief_text ?? ""}
        contentType="newsletter"
        tone={tone}
        structure={(() => {
          const counts: Record<string, number> = { title: 0, body: 0, cta: 0 }
          sections.forEach((sec: any) => (sec.components || []).forEach((c: string) => {
            if (c === "title" || c === "body" || c === "cta") counts[c] = (counts[c] || 0) + 1
          }))
          const arr: Array<{ component: string; count: number }> = [
            { component: "subject", count: 1 },
            { component: "pre_header", count: 1 },
          ]
          if (counts.title) arr.push({ component: "title", count: counts.title })
          if (counts.body) arr.push({ component: "body", count: counts.body })
          if (counts.cta) arr.push({ component: "cta", count: counts.cta })
          return arr as any
        })()}
        onApply={(optimized) => onProjectChange("brief_text", optimized)}
      />
    </div>
  )
}
