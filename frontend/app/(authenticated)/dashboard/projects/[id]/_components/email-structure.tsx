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
import { Sparkles, Loader2, CheckCircle2, Plus, X } from "lucide-react"
import { type Project } from "@/actions/projects"
import { RenderedComponent } from "../../../_components/rendered-component"
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
import { generateProjectContent } from "@/actions/projects"
import { useNotifications } from "../../../_components/notifications-provider"
import { normalizeComponentList, normalizeTranslationsMap, ensureSectionKeys } from "@/lib/section-utils"
import { ImageUploadGuard } from "./image-upload-guard"
import { useLabels } from "@/hooks/use-labels"
import { createLabel, deleteLabel } from "@/actions/labels"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

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
  onProjectChange: (field: keyof Project, value: any, silent?: boolean) => void
  onStructureChange: (
    structure: Array<{
      key: string
      name: string
      components: Array<string>
    }>
  ) => void
  onImagesChange: (images: UploadedImage[]) => void
  userName: string
  isReadOnly?: boolean
}

// Color mapping for labels based on their color property
const LABEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  red: { bg: "bg-red-500/20", text: "text-red-700 dark:text-red-300", border: "border-red-500/30" },
  blue: { bg: "bg-blue-500/20", text: "text-blue-700 dark:text-blue-300", border: "border-blue-500/30" },
  green: { bg: "bg-green-500/20", text: "text-green-700 dark:text-green-300", border: "border-green-500/30" },
  purple: { bg: "bg-purple-500/20", text: "text-purple-700 dark:text-purple-300", border: "border-purple-500/30" },
  orange: { bg: "bg-orange-500/20", text: "text-orange-700 dark:text-orange-300", border: "border-orange-500/30" },
  yellow: { bg: "bg-yellow-500/20", text: "text-yellow-700 dark:text-yellow-300", border: "border-yellow-500/30" },
  pink: { bg: "bg-pink-500/20", text: "text-pink-700 dark:text-pink-300", border: "border-pink-500/30" },
  cyan: { bg: "bg-cyan-500/20", text: "text-cyan-700 dark:text-cyan-300", border: "border-cyan-500/30" },
  gray: { bg: "bg-gray-500/20", text: "text-gray-700 dark:text-gray-300", border: "border-gray-500/30" },
}

function DynamicLabelsSection({ 
  projectLabels, 
  onToggleLabel, 
  isReadOnly 
}: { 
  projectLabels: string[]
  onToggleLabel: (label: string) => void
  isReadOnly?: boolean
}) {
  const { labels, isLoading, refresh } = useLabels()
  const [newLabelName, setNewLabelName] = useState("")
  const [newLabelColor, setNewLabelColor] = useState("gray")
  const [isCreating, setIsCreating] = useState(false)
  const [popoverOpen, setPopoverOpen] = useState(false)
  
  // Delete label state
  const [labelToDelete, setLabelToDelete] = useState<{ id: number; name: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleCreateLabel = async () => {
    if (!newLabelName.trim()) return
    
    setIsCreating(true)
    try {
      const result = await createLabel({ 
        name: newLabelName.trim().toLowerCase(),
        color: newLabelColor
      })
      
      if (result.success) {
        toast.success(`Label "${newLabelName}" created`)
        setNewLabelName("")
        setNewLabelColor("gray")
        setPopoverOpen(false)
        refresh()
      } else {
        toast.error(result.error || "Failed to create label")
      }
    } catch (error) {
      toast.error("Failed to create label")
    } finally {
      setIsCreating(false)
    }
  }
  
  const handleDeleteLabel = async () => {
    if (!labelToDelete) return
    
    setIsDeleting(true)
    try {
      const result = await deleteLabel(labelToDelete.id)
      
      if (result.success) {
        toast.success(`Label "${labelToDelete.name}" deleted`)
        refresh()
      } else {
        toast.error(result.error || "Failed to delete label")
      }
    } catch (error) {
      toast.error("Failed to delete label")
    } finally {
      setIsDeleting(false)
      setLabelToDelete(null)
    }
  }

  return (
    <>
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Project Labels</Label>
        {!isReadOnly && (
          <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">
                <Plus className="h-3 w-3 mr-1" />
                New Label
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-3" align="end">
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs">Label Name</Label>
                  <Input
                    placeholder="e.g., spring 2026"
                    value={newLabelName}
                    onChange={(e) => setNewLabelName(e.target.value)}
                    className="h-8 text-sm"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleCreateLabel()
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Color</Label>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(LABEL_COLORS).map((color) => (
                      <button
                        key={color}
                        type="button"
                        className={`w-6 h-6 rounded-full ${LABEL_COLORS[color].bg} ${
                          newLabelColor === color ? "ring-2 ring-offset-1 ring-primary" : ""
                        }`}
                        onClick={() => setNewLabelColor(color)}
                      />
                    ))}
                  </div>
                </div>
                <Button 
                  size="sm" 
                  className="w-full h-7 text-xs"
                  onClick={handleCreateLabel}
                  disabled={isCreating || !newLabelName.trim()}
                >
                  {isCreating ? <Loader2 className="h-3 w-3 animate-spin" /> : "Create Label"}
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {isLoading ? (
          <span className="text-sm text-muted-foreground">Loading labels...</span>
        ) : labels.length === 0 ? (
          <span className="text-sm text-muted-foreground">No labels available. Create one!</span>
        ) : (
          labels.map((label) => {
            const isSelected = projectLabels.includes(label.name)
            const colors = LABEL_COLORS[label.color] || LABEL_COLORS.gray
            return (
              <div key={label.id} className="group relative inline-flex">
                <Badge
                  variant={isSelected ? "default" : "outline"}
                  className={`cursor-pointer hover:opacity-80 transition-opacity pr-6 ${
                    isSelected ? `${colors.bg} ${colors.text} ${colors.border} border` : ""
                  } ${isReadOnly ? "pointer-events-none opacity-60" : ""}`}
                  onClick={() => !isReadOnly && onToggleLabel(label.name)}
                >
                  {label.name}
                </Badge>
                {!isReadOnly && (
                  <button
                    type="button"
                    className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-destructive/20"
                    onClick={(e) => {
                      e.stopPropagation()
                      setLabelToDelete({ id: label.id, name: label.name })
                    }}
                    title={`Delete "${label.name}" label`}
                  >
                    <X className="h-3 w-3 text-destructive" />
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
    
    {/* Delete Label Confirmation */}
    <AlertDialog open={!!labelToDelete} onOpenChange={(open) => !open && setLabelToDelete(null)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Label</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the label &quot;{labelToDelete?.name}&quot;? 
            This will remove it from all projects. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteLabel}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? "Deleting..." : "Delete Label"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  )
}

export function EmailStructure({
  project,
  onProjectChange,
  onStructureChange,
  onImagesChange,
  userName,
  isReadOnly = false
}: EmailStructureProps) {
  const [temperature, setTemperature] = useState(0.5)
  const [tone] = useState("professional")


  const [isGenerating, setIsGenerating] = useState(false)

  // Phase 2: Safety Guards State
  const [showImageGuard, setShowImageGuard] = useState(false)
  const [pendingGeneration, setPendingGeneration] = useState<{ type: 'all' | 'section', idx?: number } | null>(null)
  const [missingImagesCount, setMissingImagesCount] = useState(0)

  const [sections, setSections] = useState(() => {
    const initialStructure = Array.isArray(project.structure)
      ? (project.structure as Array<any>)
      : []

    if (
      initialStructure.length > 0 &&
      initialStructure[0] &&
      initialStructure[0].components
    ) {
      return ensureSectionKeys(initialStructure)
    } else {
      // Modern default structure for new/empty projects
      return ensureSectionKeys([{ 
        key: "main", 
        name: "Main Section", 
        components: ["image", "title", "body", "cta"] 
      }])
    }
  })

  // Sync sections state with project.structure updates (e.g. after SWR refetch or generation)
  useEffect(() => {
    if (project.structure && Array.isArray(project.structure) && project.structure.length > 0) {
      // Only sync if the structure actually has components (modern format)
      const firstSection = project.structure[0] as any
      if (firstSection.components) {
        setSections(ensureSectionKeys(project.structure as any))
      }
    }
  }, [project.structure])
  const [images, setImages] = useState<UploadedImage[]>([])
  const [showPromptAssistant, setShowPromptAssistant] = useState(false)
  // Check if any component has generated content (not just if components exist - image components are always created)
  const hasGeneratedContent = Array.isArray((project as any).components) && 
    ((project as any).components as any[]).some(c => c.generated_content?.trim() && c.component_type !== 'image')
  const [isTranslating, setIsTranslating] = useState(false)
  const [translatedLanguages, setTranslatedLanguages] = useState<Set<string>>(new Set())
  const [viewLang, setViewLang] = useState<string>("en")
  const { addNotification } = useNotifications()

  // Check which languages already have translations on mount/update
  useEffect(() => {
    if (project.components) {
      const langs = new Set<string>()
      project.components.forEach((c: any) => {
        const trans = normalizeTranslationsMap(c.translations)
        Object.keys(trans).forEach((l) => langs.add(l.toLowerCase()))
      })
      setTranslatedLanguages(langs)
    }
  }, [project.components])


  const toggleLabel = (label: string) => {
    const currentLabels = project.labels || []
    const newLabels = currentLabels.includes(label)
      ? currentLabels.filter((l) => l !== label)
      : [...currentLabels, label]
    onProjectChange("labels", newLabels)
  }

  const handleGenerate = async () => {
    if (!project.brief_text?.trim()) {
      toast.error("Please enter a Main Brief first")
      return
    }

    // Check that non-main sections have their own brief
    const sectionsWithoutBrief = sections.filter(s => 
      s.key !== "main" && (!s.brief || !s.brief.trim())
    )
    
    if (sectionsWithoutBrief.length > 0) {
      toast.error(
        `Section briefs required: ${sectionsWithoutBrief.map(s => s.name || s.key).join(", ")}`
      )
      return
    }

    // Check for missing images across ALL sections
    // Images are linked via image_id on the Component, not via section_key on Image
    let totalMissing = 0
    sections.forEach((section) => {
      (section.components || []).forEach((c: string) => {
        if (c === 'image') {
          // Check if there's an image component for this section with either:
          // - image_id (linked to Image table)
          // - generated_content starting with http (URL)
          // - component_url (alternative URL field)
          const hasImg = (project.components || []).some((comp: any) =>
            comp.component_type === 'image' && 
            comp.section_key === section.key && 
            (comp.image_id || comp.generated_content?.startsWith('http') || comp.component_url?.startsWith('http'))
          )
          if (!hasImg) totalMissing++
        }
      })
    })

    if (totalMissing > 0) {
      setMissingImagesCount(totalMissing)
      setPendingGeneration({ type: 'all' })
      setShowImageGuard(true)
      return
    }

    await executeGenerate()
  }

  const executeGenerate = async () => {
    setIsGenerating(true)
    try {
      // Use the project-specific generation endpoint that handles multiple sections
      // Send the current sections state so the backend has the latest briefs
      const result = await generateProjectContent(project.id, {
        count: 1,
        image_urls: images.map(img => img.url),
        structure: sections
      })

      if (result.success && result.data) {
        // Clear translation status since we have new content
        setTranslatedLanguages(new Set())

        toast.success("Content generated successfully!")
        addNotification({
          type: "success",
          title: "Generation Completed",
          message: `Generated content for all sections`
        })

        // Update components from backend response
        if (result.data.components) {
          // Use common normalization utility
          const formattedComponents = normalizeComponentList(result.data.components)
          onProjectChange("components", formattedComponents as any)
        }
      } else {
        toast.error(result.error || "Failed to generate content")
      }
    } catch (error) {
      toast.error("An unexpected error occurred during generation.")
      console.error(error)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleGenerateSection = async (idx: number) => {
    // Check for missing images in this specific section
    const section = sections[idx]
    if (!section) return

    let missing = 0;
    (section.components || []).forEach((c: string) => {
      if (c === 'image') {
        // Check if there's an image component for this section with either:
        // - image_id (linked to Image table)
        // - generated_content starting with http (URL)
        // - component_url (alternative URL field)
        const hasImg = (project.components || []).some((comp: any) =>
          comp.component_type === 'image' && 
          comp.section_key === section.key && 
          (comp.image_id || comp.generated_content?.startsWith('http') || comp.component_url?.startsWith('http'))
        )
        if (!hasImg) missing++
      }
    })

    if (missing > 0) {
      setMissingImagesCount(missing)
      setPendingGeneration({ type: 'section', idx })
      setShowImageGuard(true)
      return
    }

    await executeGenerateSection(idx)
  }

  const executeGenerateSection = async (sectionIdx: number) => {
    if (isGenerating) return
    setIsGenerating(true)

    try {
      const section = sections[sectionIdx]
      if (!section) return

      // Use the project-specific generation endpoint but ONLY for this section
      // We pass a structure containing only this section
      const result = await generateProjectContent(project.id, {
        count: 1,
        image_urls: images.map(img => img.url),
        structure: [section]
      })

      if (result.success && result.data) {
        toast.success(`Content for ${section.name} generated!`)
        
        // Update components from backend response
        if (result.data.components) {
          // Use common normalization utility
          const formattedComponents = normalizeComponentList(result.data.components)
          onProjectChange("components", formattedComponents as any)
        }
      } else {
        toast.error(result.error || "Failed to generate section content")
      }
    } catch (error) {
      toast.error("An unexpected error occurred during section generation.")
      console.error(error)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleTranslateSection = async (sectionIdx: number) => {
    if (isTranslating) return
    setIsTranslating(true)

    try {
      const section = sections[sectionIdx]
      if (!section) return

      // 1. Find components belonging to this section
      const sectionComps = (project.components || []).filter((c: any) => c.section_key === section.key)
      const textsToTranslate = sectionComps
        .filter((c: any) => c.generated_content?.trim() && c.component_type !== "image")
        .map((c: any) => ({
          // Include section_key in the key to prevent cross-section contamination
          key: `${c.section_key}:${c.component_type}${(c.component_index || 1) > 1 ? '_' + c.component_index : ''}`,
          content: c.generated_content
        }))

      if (textsToTranslate.length === 0) {
        toast.info("No text components to translate in this section.")
        return
      }

      // 2. Translate only the selected languages
      const langs = project.target_languages || []
      if (langs.length === 0) {
        toast.error("Please select target languages first")
        return
      }

      const res = await batchTranslate(textsToTranslate, langs)
      if (res.success && res.data) {
        // 3. Merge new translations with existing ones
        let failedCount = 0
        const merged = (project.components || []).map((c: any) => {
          if (c.section_key !== section.key) return c

          // Use same key format as when sending to translate
          const key = `${c.section_key}:${c.component_type}${(c.component_index || 1) > 1 ? '_' + c.component_index : ''}`
          const newTrans = (res.data as any)[key] || {}

          // Check for failure markers
          const filteredTrans = Object.fromEntries(
            Object.entries(newTrans).filter(([lang, val]) => {
              if (String(val).startsWith("__TRANSLATION_FAILED__")) {
                failedCount++
                return false
              }
              return true
            })
          )

          // Handle upper-case for CTA buttons
          const processedTrans = c.component_type === "cta"
            ? Object.fromEntries(Object.entries(filteredTrans).map(([k, v]) => [k, String(v || "").toUpperCase()]))
            : filteredTrans

          const existingTrans = normalizeTranslationsMap(c.translations)
          return { ...c, translations: { ...existingTrans, ...processedTrans } }
        })

        const normalized = normalizeComponentList(merged as any)
        onProjectChange("components", normalized as any)

        // 4. Persist to backend
        const saveRes = await saveGeneratedComponents(project.id, normalized as any)
        if (saveRes.success && saveRes.components) {
          onProjectChange("components", normalizeComponentList(saveRes.components) as any)
        }

        if (failedCount > 0) {
          toast.warning(`Section "${section.name}" translated, but ${failedCount} item(s) failed. Please retry those.`, {
            duration: 5000
          })
        } else {
          toast.success(`Section "${section.name}" translated to ${langs.length} language(s)`)
        }
      } else {
        toast.error(res.error || "Translation failed")
      }
    } catch (error) {
      toast.error("An unexpected error occurred during translation.")
      console.error(error)
    } finally {
      setIsTranslating(false)
    }
  }

  return (
    <div className="space-y-6 p-6 min-h-screen bg-[var(--bg-editor)] transition-colors duration-500">
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
              disabled={isReadOnly}
              className={isReadOnly ? "bg-muted/50 italic text-muted-foreground border-dashed opacity-100 disabled:opacity-100 dark:text-gray-400" : ""}
            />
          </div>

          {/* Project Labels */}
          <DynamicLabelsSection 
            projectLabels={project.labels || []}
            onToggleLabel={toggleLabel}
            isReadOnly={isReadOnly}
          />
        </CardContent>
      </Card>

      {/* BOTTOM SECTION: Two Columns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* LEFT COLUMN: Content Generation */}
        <Card>
          <CardHeader>
            <CardTitle>AI Generation & Strategy</CardTitle>
            <CardDescription>
              Generate premium email content using AI
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
                disabled={isReadOnly}
                className={isReadOnly ? "bg-muted/50 italic text-muted-foreground border-dashed opacity-100 disabled:opacity-100 dark:text-gray-400" : ""}
              />
            </div>

            {/* Settings Row: Creativity, Optimize, and Generate */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              {/* Creativity Level */}
              <div className="space-y-2 md:col-span-4">
                <Label>Creativity Level</Label>
                <div className="pt-2 px-1">
                  <Slider
                    value={[temperature]}
                    onValueChange={(value) => setTemperature(value[0])}
                    min={0}
                    max={1}
                    step={0.1}
                    disabled={isReadOnly}
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-1 uppercase">
                    <span>Conservative</span>
                    <span>Creative</span>
                  </div>
                </div>
              </div>

              {/* Optimize Prompt Button */}
              <div className="md:col-span-3 pb-0.5">
                <Button
                  type="button"
                  size="default"
                  variant="outline"
                  className="w-full gap-2 btn-ai-outline-coral shadow-sm h-10"
                  onClick={() => setShowPromptAssistant(true)}
                  disabled={!project.brief_text?.trim() || isReadOnly}
                >
                  <Sparkles className="h-4 w-4" />
                  <span className="text-xs">Optimize Prompt</span>
                </Button>
              </div>

              {/* Generate / Regenerate Button */}
              <div className="md:col-span-5 pb-0.5">
                <Button
                  size="default"
                  className="w-full btn-ai-coral shadow-lg hover:scale-[1.01] transition-all h-10 gap-2"
                  onClick={handleGenerate}
                  disabled={isGenerating || isReadOnly}
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  <span>{hasGeneratedContent ? "Regenerate All Content" : "Generate Content"}</span>
                </Button>
              </div>
            </div>
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

            <Separator />

            {/* Translate Selected Languages Button */}
            {((project.target_languages || []).length > 0) && hasGeneratedContent && !isReadOnly && (
              <div className="pt-2 flex justify-center">
                <Button
                  variant="outline"
                  className="w-fit px-8 text-green-600 border-green-200 bg-green-50/50 hover:bg-green-100 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800 dark:hover:bg-green-900/40 flex items-center gap-1.5"
                  disabled={isTranslating}
                  onClick={async () => {
                    try {
                      setIsTranslating(true)
                      // Include section_key in keys to prevent cross-section contamination
                      const texts = (project.components || [])
                        .filter((c: any) => c.generated_content?.trim() && c.component_type !== "image")
                        .map((c: any) => ({
                          key: `${c.section_key}:${c.component_type}${(c.component_index || 1) > 1 ? '_' + c.component_index : ''}`,
                          content: c.generated_content
                        }))

                      if (texts.length === 0) { toast.error("Generate content first"); return }
                      const langs = project.target_languages || []
                      const res = await batchTranslate(texts, langs)
                      if (res.success && res.data) {
                        const merged = (project.components || []).map((c: any) => {
                          const key = `${c.section_key}:${c.component_type}${(c.component_index || 1) > 1 ? '_' + c.component_index : ''}`
                          const rawT = (res.data as any)[key] || {}
                          const t = c.component_type === "cta"
                            ? Object.fromEntries(Object.entries(rawT).map(([k, v]) => [k, String(v || "").toUpperCase()]))
                            : rawT
                          const curr = normalizeTranslationsMap(c.translations)
                          return { ...c, translations: { ...curr, ...t } }
                        })
                        const normalized = normalizeComponentList(merged as any)
                        onProjectChange("components", normalized as any)
                        const saveRes = await saveGeneratedComponents(project.id, normalized as any)

                        if (saveRes.success && saveRes.components) {
                          const fromBackend = normalizeComponentList(saveRes.components)
                          onProjectChange("components", fromBackend as any)
                        }

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
                    "Translate All"
                  )}
                </Button>
              </div>
            )}


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

          // Optimistically update the UI for responsiveness (silent: true to avoid triggering autosave loop)
          onProjectChange("components", normalized as any, true)

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
            const normalizedFromBackend = normalizeComponentList(result.components)
            // DEFINITIVE UPDATE: silent: true because we just saved them
            onProjectChange("components", normalizedFromBackend as any, true)
            // Also update images if the backend returned them
            if (result.images) {
              onProjectChange("images", result.images as any, true)
            }
          }
        }}
        onUpdateComponent={(type, index, content, sectionKey) => {
          const list: any[] = [...((project.components as any) || [])]
          const idx = list.findIndex((c: any) => 
            c.component_type === type && 
            (c.component_index || 1) === index &&
            (!sectionKey || c.section_key === sectionKey)
          )
          const finalContent = type === "cta" ? (content || "").toUpperCase() : content
          if (idx >= 0) {
            list[idx] = { ...list[idx], generated_content: finalContent }
          } else {
            list.push({ 
              component_type: type, 
              component_index: index, 
              generated_content: finalContent, 
              translations: {},
              section_key: sectionKey || "default"
            })
          }
          const normalized = normalizeComponentList(list as any)
          onProjectChange("components", normalized as any)
        }}
        onGenerateSection={handleGenerateSection}
        isGenerating={isGenerating}
        onTranslateSection={handleTranslateSection}
        isTranslating={isTranslating}
        isReadOnly={isReadOnly}
        languageFlags={
          <div className="flex flex-wrap gap-2">
            {[{ value: "en", label: "English", flag: "🇬🇧" }, ...LANGUAGES.filter(l => (project.target_languages || []).includes(l.value))].map((l) => {
              const isTranslated = l.value === "en" || translatedLanguages.has(l.value)
              const showSpinner = isTranslating && l.value !== "en"

              return (
                <Badge
                  key={l.value}
                  variant={viewLang === l.value ? "default" : "outline"}
                  className={`cursor-pointer gap-1.5 px-3 py-1 text-xs transition-all ${viewLang === l.value ? 'ring-2 ring-primary/20 scale-105' : 'hover:bg-accent/50'}`}
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
        }
        onProjectChange={onProjectChange}
      />

      {/* Phase 2: Image Upload Guard */}
      <ImageUploadGuard
        isOpen={showImageGuard}
        missingCount={missingImagesCount}
        onClose={() => {
          setShowImageGuard(false)
          setPendingGeneration(null)
        }}
        onConfirm={async () => {
          setShowImageGuard(false)
          if (pendingGeneration?.type === 'all') {
            await executeGenerate()
          } else if (pendingGeneration?.type === 'section' && pendingGeneration.idx !== undefined) {
            await executeGenerateSection(pendingGeneration.idx)
          }
          setPendingGeneration(null)
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
    </div >
  )
}
