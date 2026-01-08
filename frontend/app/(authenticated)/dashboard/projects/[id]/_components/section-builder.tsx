"use client"

import React, { useMemo, useEffect, useState } from "react"
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
  type DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { uploadImage } from "@/actions/upload"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import { createPushFromSection } from "@/actions/projects"
import imageCompression from "browser-image-compression"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Edit2, Copy, FileCode, Check, Sparkles, Languages, Bell } from "lucide-react"
import { Loader2 } from "lucide-react"
import { generate } from "@/actions/generate"
import { handlebarsGenerate } from "@/actions/export"
import { batchTranslate } from "@/actions/translate"
import {
  ensureSectionKeys,
  findComponentForSection,
  findImageForSection,
  isMainSection,
  normalizeImage,
  normalizeTranslationsMap,
  type Section,
  type SectionComponent,
  type UploadedImage,
} from "@/lib/section-utils"
import { PromptAssistantDialog } from "../../../_components/prompt-assistant-dialog"
import { Button } from "@/components/ui/button"

/**
 * Input component with local state to prevent focus loss on parent re-render
 * Propagates changes only on blur, not on every keystroke
 */
function SectionNameInput({
  value,
  onChange,
  placeholder,
  className,
  disabled = false,
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}) {
  const [localValue, setLocalValue] = useState(value)

  // Sync local state when prop changes (e.g., from external updates)
  useEffect(() => {
    setLocalValue(value)
  }, [value])

  return (
    <input
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onBlur={() => {
        if (localValue !== value) {
          onChange(localValue)
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.currentTarget.blur()
        }
      }}
      placeholder={placeholder}
      className={className}
      disabled={disabled}
    />
  )
}

/**
 * Textarea component for section brief with local state
 * Propagates changes only on blur, not on every keystroke
 */
function SectionBriefInput({
  value,
  onChange,
  placeholder,
  className,
  disabled = false,
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}) {
  const [localValue, setLocalValue] = useState(value)

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  return (
    <textarea
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onBlur={() => {
        if (localValue !== value) {
          onChange(localValue)
        }
      }}
      placeholder={placeholder}
      className={className}
      rows={2}
      disabled={disabled}
    />
  )
}

export function SectionBuilder({
  value,
  onChange,
  projectId,
  onImagesChange,
  components,
  projectImages,
  brief,
  tone,
  onUpdateComponent,
  currentLanguage = "en",
  targetLanguages = [],
  onUpdateComponents,
  onGenerateSection,
  isGenerating = false,
  onTranslateSection,
  isTranslating = false,
  languageFlags,
  isReadOnly = false,
  onProjectChange,
  contentType = "newsletter",
}: {
  value: Section[]
  onChange: (next: Section[]) => void
  projectId: number
  onImagesChange?: (images: UploadedImage[]) => void
  components?: SectionComponent[]
  projectImages?: UploadedImage[]
  brief?: string
  tone?: string
  onUpdateComponent?: (type: string, index: number, content: string, sectionKey?: string) => void
  currentLanguage?: string
  targetLanguages?: string[]
  onUpdateComponents?: (list: SectionComponent[]) => void
  onGenerateSection?: (sectionIdx: number) => Promise<void>
  isGenerating?: boolean
  onTranslateSection?: (sectionIdx: number) => Promise<void>
  isTranslating?: boolean
  languageFlags?: React.ReactNode
  isReadOnly?: boolean
  onProjectChange?: (field: any, value: any, silent?: boolean) => void
  contentType?: "newsletter" | "push_notification"
}) {
  const componentsPalette = [
    { id: "title", label: "Title" },
    { id: "body", label: "Body" },
    { id: "cta", label: "CTA" },
    { id: "image", label: "Image" },
  ]

  // Derive imagesBySection from props (no state to avoid race conditions)
  const imagesBySection = useMemo<Record<string, UploadedImage[][]>>(() => {
    if (!projectImages || !components || value.length === 0) {
      return {};
    }

    const result: Record<string, UploadedImage[][]> = {}

    // For each section, find its image components by section_key or section_order
    for (let sectionIdx = 0; sectionIdx < value.length; sectionIdx++) {
      const section = value[sectionIdx]
      result[section.key] = []

      // Count components within THIS section only (for component_index within section)
      const sectionCounters: Record<string, number> = {}

      for (const compType of section.components) {
        sectionCounters[compType] = (sectionCounters[compType] || 0) + 1
        const componentIndexInSection = sectionCounters[compType]

        // Find component matching type AND section (not global index)
        const comp = components.find(c =>
          c.component_type === compType &&
          (c.section_key === section.key || c.section_order === sectionIdx)
        )

        let image: UploadedImage | undefined = comp?.image as UploadedImage | undefined

        if (!image && comp?.image_id && projectImages) {
          const foundImage = projectImages.find(img => Number(img.id) === comp.image_id)
          if (foundImage) {
            image = normalizeImage(foundImage)
          }
        }

        if (compType === "image" && image && image.url) {
          result[section.key].push([{ id: String(image.id), url: image.url, filename: image.filename }])
        } else {
          result[section.key].push([])
        }
      }
    }
    return result
  }, [components, value, projectImages])


  const addSection = () => {
    const next: Section[] = ensureSectionKeys([
      ...value,
      {
        key: "",
        name: "",
        components: ["image", "title", "body", "cta"],  // Default components for new sections
      },
    ])
    onChange(next)
  }

  const renameSection = (idx: number, name: string) => {
    const next = value.slice()
    next[idx] = { ...next[idx], name }
    onChange(ensureSectionKeys(next))
  }

  const updateSectionBrief = (idx: number, brief: string) => {
    const next = value.slice()
    next[idx] = { ...next[idx], brief }
    onChange(ensureSectionKeys(next))
  }

  const removeSection = (idx: number) => {
    const next = value.slice()
    const removed = next.splice(idx, 1)[0]
    onChange(ensureSectionKeys(next))
  }

  const addComponent = (idx: number, comp: string) => {
    if (!comp) return
    const next = value.slice()
    const section = next[idx]
    next[idx] = { ...section, components: [...section.components, comp] }
    onChange(ensureSectionKeys(next))
  }

  const removeComponentAt = (idx: number, compIdx: number) => {
    const next = value.slice()
    const section = next[idx]
    const comps = section.components.slice()
    comps.splice(compIdx, 1)
    next[idx] = { ...section, components: comps }
    onChange(ensureSectionKeys(next))
  }

  // ---- Drag and Drop (Sections) ----
  const sectionIds = useMemo(() => ensureSectionKeys(value).map((s) => `section:${s.key}`), [value])
  const sensors = useSensors(useSensor(PointerSensor))

  const onSectionsDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!active?.id || !over?.id) return
    const from = sectionIds.indexOf(String(active.id))
    const to = sectionIds.indexOf(String(over.id))
    if (from === -1 || to === -1 || from === to) return
    const next = arrayMove(ensureSectionKeys(value), from, to)
    onChange(next)
  }

  function SortableSectionItem({ id, children }: { id: string; children: React.ReactNode }) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
      id,
      disabled: isReadOnly
    })
    const style: React.CSSProperties = {
      transform: CSS.Transform.toString(transform),
      transition,
    }
    return (
      <div ref={setNodeRef} style={style} className="rounded-md border border-border p-3 bg-card/50">
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing touch-none -mt-1 -mb-1 mb-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Drag to reorder
        </div>
        {children}
      </div>
    )
  }

  function SortableComponentItem({ id, children }: { id: string; children: (p: { attributes: any; listeners: any }) => React.ReactNode }) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
      id,
      disabled: isReadOnly
    })
    const style: React.CSSProperties = {
      transform: CSS.Transform.toString(transform),
      transition,
    }
    return (
      <div
        ref={setNodeRef}
        style={style}
        className="block"
      >
        {children({ attributes, listeners })}
      </div>
    )
  }

  const compressImage = async (file: File): Promise<File> => {
    if (file.size < 100 * 1024) return file
    try {
      const options = {
        maxSizeMB: 2,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        fileType: "image/jpeg",
        initialQuality: 0.8,
      }
      return await imageCompression(file, options)
    } catch {
      return file
    }
  }

  const handleUploadToComponent = async (sectionKey: string, compIdx: number, files: File[]) => {
    const file = files[0]
    if (!file) return

    try {
      const compressed = await compressImage(file)
      const res = await uploadImage(projectId, compressed)
      if (!res.success || !res.data) throw new Error(res.error || "Upload failed")

      const uploaded = normalizeImage(res.data)

      // Find section and component type
      const sectionIdx = value.findIndex(s => s.key === sectionKey)
      if (sectionIdx === -1) return

      const section = value[sectionIdx]
      const targetType = section.components[compIdx]
      if (!targetType) return

      if (onUpdateComponents) {
        const list = (components || []).slice()

        // Find existing component matching type AND section (same logic as imagesBySection)
        const existingIndex = list.findIndex(c =>
          c.component_type === targetType &&
          (c.section_key === sectionKey || c.section_order === sectionIdx)
        )

        let updatedComponent: SectionComponent;

        if (existingIndex > -1) {
          // Update existing
          updatedComponent = {
            ...list[existingIndex],
            image_id: Number(uploaded.id),
            image: uploaded,
            section_key: sectionKey,
            section_order: sectionIdx
          };
          list[existingIndex] = updatedComponent as any;
        } else {
          // Create new
          updatedComponent = {
            component_type: targetType,
            component_index: 1,  // Per-section index, always 1 for single image per section
            generated_content: "",
            image_id: Number(uploaded.id),
            image: uploaded,
            translations: {},
            section_key: sectionKey,
            section_order: sectionIdx,
          };
          list.push(updatedComponent as any);
        }
        
        // 1. Optimistic UI update
        await onUpdateComponents(list as any)
        
        // 2. Immediate persist to backend for this specific component
        const { saveGeneratedComponents } = await import("@/actions/components")
        const saveResult = await saveGeneratedComponents(projectId, [
          {
            component_type: updatedComponent.component_type,
            component_index: updatedComponent.component_index,
            generated_content: updatedComponent.generated_content || "",
            image_id: updatedComponent.image_id,
            section_key: sectionKey,
            section_order: sectionIdx,
            translations: {}
          }
        ] as any)
        
        if (saveResult.success && saveResult.components) {
          // 3. Silent update of the global state with backend data
          if (onProjectChange) {
            onProjectChange("components", saveResult.components, true)
          }
          toast.success("Image uploaded successfully")
        }
      }

    } catch (e) {
      toast.error("Image upload failed.")
    }
  }

  const removeImageFromComponent = async (sectionKey: string, compIdx: number, imageId: string) => {
    // Find section and component type
    const sectionIdx = value.findIndex(s => s.key === sectionKey)
    if (sectionIdx === -1) return

    const section = value[sectionIdx]
    const targetType = section.components[compIdx]
    if (!targetType) return

    if (onUpdateComponents) {
      const list = (components || []).slice()

      // Find component matching type AND section (same logic as imagesBySection)
      const existingIndex = list.findIndex(c =>
        c.component_type === targetType &&
        (c.section_key === sectionKey || c.section_order === sectionIdx)
      )

      if (existingIndex > -1) {
        const updatedComponent = { ...list[existingIndex], image_id: undefined, image: undefined };
        list[existingIndex] = updatedComponent;
        
        // 1. Optimistic UI update
        onUpdateComponents(list as any)
        
        // 2. Persist removal to backend
        const { saveGeneratedComponents } = await import("@/actions/components")
        await saveGeneratedComponents(projectId, [
          {
            component_type: updatedComponent.component_type,
            component_index: updatedComponent.component_index,
            generated_content: updatedComponent.generated_content || "",
            image_id: undefined,
            section_key: sectionKey,
            section_order: sectionIdx,
            translations: {}
          }
        ] as any)
      }
    }
  }

  const renderTextWithLinks = (value: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g
    const parts = value.split(urlRegex)
    return parts.map((part, i) => {
      if (urlRegex.test(part)) {
        return (
          <a
            key={`lnk-${i}`}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline hover:underline break-all"
          >
            {part}
          </a>
        )
      }
      return <span key={`txt-${i}`}>{part}</span>
    })
  }

  const renderPreview = (type: string, _displayIndex: number, sectionKey?: string, sectionOrder?: number) => {
    // Find component using simplified lookup (section_key primary, section_order fallback)
    const found = sectionKey 
      ? findComponentForSection(components || [], sectionKey, sectionOrder ?? 0, type)
      : components?.find(c => c.component_type === type)

    const text = (() => {
      if (!found) return ""
      if (currentLanguage && currentLanguage !== "en") {
        const transMap = normalizeTranslationsMap(found.translations)
        const t = transMap[currentLanguage.toLowerCase()]
        if (t && t.trim()) return t
      }
      return found.generated_content || ""
    })()

    if (text.trim()) {
      if (type === "cta") {
        return (
          <div className="inline-flex rounded-md bg-primary text-primary-foreground px-4 py-2 text-xs font-semibold shadow-sm">
            {text.toUpperCase()}
          </div>
        )
      }
      return (
        <p className="text-sm leading-6 whitespace-pre-wrap break-words">
          {renderTextWithLinks(text)}
        </p>
      )
    }

    // Fallback placeholder skeletons
    if (type === "subject" || type === "pre_header") {
      return (
        <div className="h-3.5 w-2/3 rounded bg-muted-foreground/20" />
      )
    }
    if (type === "title") {
      return (
        <div className="space-y-2">
          <div className="h-4 w-2/3 rounded bg-muted-foreground/20" />
        </div>
      )
    }
    if (type === "body") {
      return (
        <div className="space-y-1.5">
          <div className="h-2.5 w-full rounded bg-muted-foreground/15" />
          <div className="h-2.5 w-11/12 rounded bg-muted-foreground/15" />
          <div className="h-2.5 w-10/12 rounded bg-muted-foreground/15" />
        </div>
      )
    }
    if (type === "cta") {
      return (
        <div className="inline-flex rounded-md bg-primary text-primary-foreground px-4 py-2 text-[11px] font-semibold shadow-sm">
          CTA Button
        </div>
      )
    }
    return null
  }

  const [editing, setEditing] = useState<Record<string, boolean>>({})
  const [editValues, setEditValues] = useState<Record<string, string>>({})
  const [regenBusy, setRegenBusy] = useState<Record<string, boolean>>({})
  const [generatingSections, setGeneratingSections] = useState<Record<number, boolean>>({})
  const [translatingSections, setTranslatingSections] = useState<Record<number, boolean>>({})
  const [creatingPushSections, setCreatingPushSections] = useState<Record<number, boolean>>({})
  const [optimizationSectionIdx, setOptimizationSectionIdx] = useState<number | null>(null)
  const router = useRouter()

  const handleCopy = async (text: string) => {
    if (!text?.trim()) {
      toast.error("Nothing to copy")
      return
    }
    try {
      await navigator.clipboard.writeText(text)
      toast.success("Copied to clipboard")
    } catch (err) {
      console.error("Copy failed:", err)
      toast.error("Failed to copy - try selecting and copying manually")
    }
  }

  const handleCopyHandlebar = async (
    key: string,
    englishFallback: string,
    translations?: Record<string, string>
  ) => {
    try {
      const res = await handlebarsGenerate({
        project_id: projectId,
        component_key: key,
        translations: translations || {},
        english_fallback: englishFallback || "",
      })
      if (res.success && res.data?.handlebar_template) {
        try {
          await navigator.clipboard.writeText(res.data.handlebar_template)
          toast.success("Handlebar copied to clipboard")
        } catch {
          toast.message("Handlebar ready", {
            description: "Clipboard unavailable. Click to copy manually.",
          })
        }
      } else {
        toast.error(res.error || "Failed to generate handlebar")
      }
    } catch (e) {
      toast.error("Error generating handlebar")
    }
  }

  return (
    <Card className="mx-auto max-w-[840px] bg-card shadow-xl ring-1 ring-border/5 transition-colors">
      <CardHeader className="pb-4">
        <div className="flex flex-col gap-3">
          <div>
            <CardTitle className="text-2xl">
              {contentType === "push_notification" ? "Push Notification" : "Email Structure"}
            </CardTitle>
            <CardDescription>
              {contentType === "push_notification" 
                ? "Configure your push notification content."
                : "Arrange sections and components. Preview mirrors the output style."}
            </CardDescription>
          </div>
          {languageFlags && (
            <div className="flex flex-wrap gap-2 pt-1 border-t mt-1">
              {languageFlags}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-6 sm:px-8 md:px-10 py-8 bg-background transition-colors">

        {/* Fixed header components (visual only) - Only for newsletters */}
        {contentType === "newsletter" && (
        <div className="mb-6 rounded-lg border border-primary/10 bg-accent/30 p-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Header (always included)</div>
          <div className="mt-3 space-y-3">
            {(() => {
              const headerItems: Array<{ label: string; type: "subject" | "pre_header" }> = [
                { label: "Subject", type: "subject" },
                { label: "Pre-header", type: "pre_header" },
              ]
              return headerItems.map(({ label, type }) => {
                const displayIndex = 1
                // Look specifically for components in the 'header' section
                const found = components?.find(
                  (c) => c.component_type === type && 
                         (c.section_key === "header" || c.section_key === "default")
                )
                const currentText = (() => {
                  if (!found) return ""
                  if (currentLanguage && currentLanguage !== "en") {
                    const transMap = normalizeTranslationsMap((found as any).translations)
                    const t = transMap[currentLanguage.toLowerCase()]
                    // Safe guard: check if translation exists and is not a failure marker
                    if (t && String(t).trim() && !String(t).includes("__TRANSLATION_FAILED__")) {
                      return String(t)
                    }
                    return `[Missing translation: ${currentLanguage.toUpperCase()}]`
                  }
                  return found.generated_content || ""
                })()
                const compKey = `header:${type}:${displayIndex}`
                const isEditing = !!editing[compKey]
                const editText = editValues[compKey] ?? currentText
                return (
                  <div key={type} className="rounded-xl border border-border bg-card p-4 space-y-2 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs px-2 py-0.5">{label}</Badge>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                          disabled={!!regenBusy[compKey] || !brief || isReadOnly}
                          onClick={async () => {
                            if (!brief) return
                            setRegenBusy(v => ({ ...v, [compKey]: true }))
                            try {
                              const result = await generate({
                                project_id: projectId,
                                text: brief!,
                                count: 1,
                                tone: tone || "professional",
                                content_type: "newsletter",
                                structure: [{ component: type as any, count: 1 }],
                                temperature: 0.7,
                                use_few_shot: true,
                                use_flash: true,
                              })
                              if (result.success && result.data) {
                                const val = String(result.data.variations[0][type] || "")

                                if (val && onUpdateComponents) {
                                  // Check if this component had existing translations
                                  const existingComp = (components || []).find((c) => 
                                    c.component_type === type && 
                                    ((c as any).section_key === "header" || (c as any).section_key === "default")
                                  )
                                  const hadTranslations = existingComp?.translations && typeof existingComp.translations === 'object' && Object.keys(existingComp.translations).length > 0

                                  // If component had translations and target languages are set, retranslate
                                  if (hadTranslations && (targetLanguages || []).length > 0) {
                                    try {
                                      // Include section_key in key to match email-structure.tsx format
                                      const translationKey = `header:${type}`
                                      const texts = [{ key: translationKey, content: val }]
                                      const langs = targetLanguages || []
                                      const res = await batchTranslate(texts, langs)

                                      if (res.success && res.data) {
                                        const t = (res.data[translationKey] || {}) as Record<string, string>

                                        const merged = (components || []).map((c) => {
                                          if (c.component_type === type && 
                                              ((c as any).section_key === "header" || (c as any).section_key === "default")) {
                                            return { ...c, generated_content: val, translations: t, section_key: "header" }
                                          }
                                          return c
                                        })
                                        onUpdateComponents(merged as any)
                                      }
                                    } catch (err) {
                                      console.error(`Error retranslating ${type}:`, err)
                                    }
                                  } else {
                                    // No translations to regenerate, just update English content
                                    const merged = (components || []).map((c) => {
                                      if (c.component_type === type && 
                                          ((c as any).section_key === "header" || (c as any).section_key === "default")) {
                                        return { ...c, generated_content: val, section_key: "header" }
                                      }
                                      return c
                                    })
                                    onUpdateComponents(merged as any)
                                  }
                                }
                              }
                            } finally {
                              setRegenBusy(v => ({ ...v, [compKey]: false }))
                            }
                          }}
                        >
                          {regenBusy[compKey] ? (
                            <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                          ) : (
                            <RefreshCw className="h-3.5 w-3.5 mr-1" />
                          )}
                          {found?.generated_content?.trim() ? "Regenerate" : "Generate"}
                        </button>
                        {!isReadOnly && (
                          <button
                            type="button"
                            className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                            onClick={() => setEditing(v => ({ ...v, [compKey]: !v[compKey] }))}
                          >
                            <Edit2 className="h-3.5 w-3.5 mr-1" /> Edit
                          </button>
                        )}
                        <button
                          type="button"
                          className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                          onClick={() => {
                            const textToCopy = (() => {
                              if (!found) return ""
                              if (currentLanguage && currentLanguage !== "en") {
                                const t = (found as any).translations?.[currentLanguage]
                                if (t && String(t).trim()) return String(t)
                              }
                              return currentText
                            })()
                            handleCopy(textToCopy)
                          }}
                          disabled={!currentText && !(found && (found as any).translations && (found as any).translations[currentLanguage || ""])}
                        >
                          <Copy className="h-3.5 w-3.5 mr-1" /> Copy
                        </button>
                        <button
                          type="button"
                          className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                          onClick={() => {
                            const en = (found?.generated_content || "")
                            const trAny = (found as any)?.translations
                            const trRaw = (trAny && typeof trAny === "object" && !Array.isArray(trAny)) ? trAny : {}
                            const allowed = new Set((targetLanguages || []).map(l => String(l).toLowerCase()))
                            const tr = Object.fromEntries(
                              Object.entries(trRaw)
                                .filter(([k]) => allowed.has(String(k).toLowerCase()))
                                .map(([k, v]) => [k, String(v ?? "")])
                            ) as Record<string, string>
                            handleCopyHandlebar(type, en, tr)
                          }}
                          disabled={!((found?.generated_content || "").trim())}
                        >
                          <FileCode className="h-3.5 w-3.5 mr-1" /> Handlebar
                        </button>
                      </div>
                    </div>

                    {/* Content Display */}
                    {isEditing ? (
                      <div className="space-y-2">
                        <textarea
                          value={editText}
                          onChange={(e) => setEditValues(v => ({ ...v, [compKey]: e.target.value }))}
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          rows={2}
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            className="text-xs px-3 py-1.5 rounded hover:bg-muted font-medium text-muted-foreground"
                            onClick={() => setEditing(v => ({ ...v, [compKey]: false }))}
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground font-medium hover:bg-primary/90"
                            onClick={() => {
                              if (onUpdateComponent) {
                                onUpdateComponent(type, 1, editText, "header")
                              }
                              setEditing(v => ({ ...v, [compKey]: false }))
                            }}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className={`rounded-md border p-3 text-sm ${currentText ? 'bg-background border-border/40' : 'bg-muted/10 border-transparent text-muted-foreground italic'}`}>
                        {currentText || "No content generated yet."}
                      </div>
                    )}
                  </div>
                )
              })
            })()}
          </div>
        </div>
        )}

        {/* Sections DnD */}
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onSectionsDragEnd}>
          <SortableContext items={sectionIds} strategy={verticalListSortingStrategy}>
            <div className="space-y-3">
              {(() => {
                return ensureSectionKeys(value).map((section, idx) => {
                  // Count components within THIS section only (for internal section indexing)
                  const sectionTypeCounters: Record<string, number> = {}
                  
                  return (
                    <SortableSectionItem key={`section:${section.key}`} id={`section:${section.key}`}>
                      {/* ... content ... */}
                      {/* (Skipping unrelated lines, focusing on the component loop below) */}

                      {/* Use existing lines until the component map */}
                      <div className="flex items-center gap-2">
                        <SectionNameInput
                          value={section.name}
                          onChange={(name) => renameSection(idx, name)}
                          placeholder={`Section ${idx + 1} name`}
                          className={`w-full rounded-md border bg-background px-2 py-1 text-sm ${isMainSection(section) ? 'opacity-70 cursor-not-allowed select-none italic font-medium bg-muted/50' : ''}`}
                          disabled={isMainSection(section) || isReadOnly}
                        />
                        {/* Section-level Generate/Translate buttons - only for newsletters (multi-section) */}
                        {contentType === "newsletter" && (
                          <>
                            <button
                              type="button"
                              className="rounded-md px-2 py-1 text-xs flex items-center gap-1 btn-ai-coral shadow-sm hover:scale-[1.02] transition-all"
                              disabled={isGenerating || generatingSections[idx] || isReadOnly}
                              onClick={async () => {
                                if (!onGenerateSection) return
                                setGeneratingSections(prev => ({ ...prev, [idx]: true }))
                                try {
                                  await onGenerateSection(idx)
                                } finally {
                                  setGeneratingSections(prev => ({ ...prev, [idx]: false }))
                                }
                              }}
                            >
                              {generatingSections[idx] ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Sparkles className="h-3 w-3" />
                              )}
                              {(() => {
                                // Check if this specific section has ANY generated content
                                const hasSectionContent = section.components.some(type => {
                                  const comp = findComponentForSection(components || [], section.key, idx, type)
                                  return !!comp?.generated_content
                                })
                                return hasSectionContent ? "Regenerate" : "Generate"
                              })()}
                            </button>
                            <button
                              type="button"
                              className="rounded-md border px-2 py-1 text-xs hover:bg-accent flex items-center gap-1 bg-green-50 text-green-700 border-green-200"
                              disabled={isTranslating || translatingSections[idx] || section.components.length === 0 || isReadOnly}
                              onClick={async () => {
                                if (!onTranslateSection) return
                                setTranslatingSections(prev => ({ ...prev, [idx]: true }))
                                try {
                                  await onTranslateSection(idx)
                                } finally {
                                  setTranslatingSections(prev => ({ ...prev, [idx]: false }))
                                }
                              }}
                            >
                              {translatingSections[idx] ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Languages className="h-3 w-3" />
                              )}
                              Translate
                            </button>
                          </>
                        )}
                        {contentType === "newsletter" && (
                          <button
                            type="button"
                            className="rounded-md border px-2 py-1 text-xs hover:bg-accent flex items-center gap-1 bg-purple-50 text-purple-700 border-purple-200"
                            disabled={creatingPushSections[idx] || isReadOnly}
                            onClick={async () => {
                              setCreatingPushSections(prev => ({ ...prev, [idx]: true }))
                              try {
                                const result = await createPushFromSection(projectId, section.key)
                                if (result.success && result.data) {
                                  toast.success("Push notification created!")
                                  router.replace(`/push/projects/${result.data.id}`)
                                } else {
                                  toast.error(result.error || "Failed to create push")
                                }
                              } catch (e) {
                                toast.error("Failed to create push notification")
                              } finally {
                                setCreatingPushSections(prev => ({ ...prev, [idx]: false }))
                              }
                            }}
                            title="Create a push notification from this section"
                          >
                            {creatingPushSections[idx] ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Bell className="h-3 w-3" />
                            )}
                            Push
                          </button>
                        )}
                        {!isMainSection(section) && (
                          <button
                            type="button"
                            className="rounded-md border px-2 py-1 text-xs hover:bg-destructive hover:text-destructive-foreground transition-colors disabled:opacity-30 disabled:pointer-events-none"
                            onClick={() => removeSection(idx)}
                            aria-label="Remove section"
                            disabled={isReadOnly}
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      {!isMainSection(section) && (
                        <div className="mt-2 group">
                          {(() => {
                            const hasSectionContent = section.components.some(type => {
                              const comp = findComponentForSection(components || [], section.key, idx, type)
                              return !!comp?.generated_content
                            })

                            if (hasSectionContent) {
                              return (
                                <details className="cursor-pointer">
                                  <summary className="text-[11px] text-muted-foreground uppercase tracking-wider font-semibold hover:text-foreground transition-colors py-1 flex items-center gap-1">
                                    <span>Brief for this section</span>
                                    <Edit2 className="h-2.5 w-2.5" />
                                  </summary>
                                  <div className="pt-2">
                                    <div className="flex gap-2 items-start">
                                      <SectionBriefInput
                                        value={section.brief || ''}
                                        onChange={(brief) => updateSectionBrief(idx, brief)}
                                        placeholder={`Brief for ${section.name || 'this section'}... (optional - will use main brief if empty)`}
                                        className={`w-full rounded-md border bg-background px-2 py-1 text-sm resize-none ${isReadOnly ? 'bg-muted/50 italic text-muted-foreground opacity-100 disabled:opacity-100 dark:text-gray-400' : ''}`}
                                        disabled={isReadOnly}
                                      />
                                      {!isReadOnly && (
                                        <Button
                                          variant="ghost"
                                          size="icon"
                                          className="h-8 w-8 shrink-0 text-muted-foreground hover:text-primary"
                                          onClick={() => setOptimizationSectionIdx(idx)}
                                          title="Optimize with AI"
                                        >
                                          <Sparkles className="h-4 w-4" />
                                        </Button>
                                      )}
                                    </div>
                                  </div>
                                </details>
                              )
                            }

                            return (
                              <div className="flex gap-2 items-start">
                                <SectionBriefInput
                                  value={section.brief || ''}
                                  onChange={(brief) => updateSectionBrief(idx, brief)}
                                  placeholder={`Brief for ${section.name || 'this section'}... (optional - will use main brief if empty)`}
                                  className={`w-full rounded-md border bg-background px-2 py-1 text-sm resize-none ${isReadOnly ? 'bg-muted/50 italic text-muted-foreground opacity-100 disabled:opacity-100 dark:text-gray-400' : ''}`}
                                  disabled={isReadOnly}
                                />
                                {!isReadOnly && (
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 shrink-0 text-muted-foreground hover:text-primary"
                                    onClick={() => setOptimizationSectionIdx(idx)}
                                    title="Optimize with AI"
                                  >
                                    <Sparkles className="h-4 w-4" />
                                  </Button>
                                )}
                              </div>
                            )
                          })()}
                        </div>
                      )}

                      {/* Push Notification Preview - Modern iPhone style */}
                      {contentType === "push_notification" ? (
                        <div className="mt-4 flex flex-col lg:flex-row gap-6">
                          {/* iPhone mockup */}
                          <div className="mx-auto lg:mx-0 flex-shrink-0">
                            <div className="relative w-[280px]">
                              {/* iPhone frame - modern style with Dynamic Island */}
                              <div className="bg-black rounded-[3rem] p-[10px] shadow-2xl">
                                {/* Screen */}
                                <div className="bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 rounded-[2.5rem] overflow-hidden relative">
                                  {/* Dynamic Island */}
                                  <div className="absolute top-3 left-1/2 -translate-x-1/2 w-[90px] h-[28px] bg-black rounded-full z-10"></div>
                                  
                                  {/* Status bar */}
                                  <div className="flex justify-between items-center px-8 pt-4 pb-2 text-white text-xs font-medium">
                                    <span>9:41</span>
                                    <div className="flex items-center gap-1">
                                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3C8.5 3 5.5 4.5 3.5 7L12 18l8.5-11C18.5 4.5 15.5 3 12 3z"/></svg>
                                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M2 17h2v4H2v-4zm4-5h2v9H6v-9zm4-4h2v13h-2V8zm4-3h2v16h-2V5z"/></svg>
                                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17 4h-3V2h-4v2H7v18h10V4z"/></svg>
                                    </div>
                                  </div>
                                  
                                  {/* Notification area - with padding for Dynamic Island */}
                                  <div className="px-3 pt-6 pb-40 space-y-2">
                                    {/* Push Notification Card */}
                                    <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl rounded-2xl shadow-xl overflow-hidden">
                                      {/* App header */}
                                      <div className="flex items-center gap-2 px-3 py-2">
                                        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center shadow-sm">
                                          <span className="text-white text-xs font-bold">L</span>
                                        </div>
                                        <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200 tracking-wide">LUISAVIAROMA</span>
                                        <span className="text-[10px] text-gray-400 ml-auto">now</span>
                                      </div>
                                      
                                      {/* Notification content */}
                                      <div className="px-3 pb-3 space-y-1">
                                        {/* Title Preview */}
                                        {(() => {
                                          const titleComp = findComponentForSection(components || [], section.key, idx, "title", 1)
                                          const titleText = titleComp?.generated_content || ""
                                          return (
                                            <p className={`font-semibold text-[13px] text-gray-900 dark:text-white leading-tight ${!titleText && 'text-gray-300 italic'}`}>
                                              {titleText || "Push title here..."}
                                            </p>
                                          )
                                        })()}
                                        
                                        {/* Body Preview */}
                                        {(() => {
                                          const bodyComp = findComponentForSection(components || [], section.key, idx, "body", 1)
                                          const bodyText = bodyComp?.generated_content || ""
                                          return (
                                            <p className={`text-[12px] text-gray-600 dark:text-gray-300 leading-snug ${!bodyText && 'text-gray-300 italic'}`}>
                                              {bodyText || "Push body text here..."}
                                            </p>
                                          )
                                        })()}
                                      </div>
                                    </div>
                                  </div>
                                  
                                  {/* Home indicator */}
                                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-32 h-1 bg-white/50 rounded-full"></div>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Editor Panel */}
                          <div className="flex-1 space-y-4">
                            <div className="text-sm text-muted-foreground mb-2">
                              Edit your push notification content below:
                            </div>
                            
                            {/* Title Editor */}
                            {(() => {
                              const titleComp = findComponentForSection(components || [], section.key, idx, "title", 1)
                              const titleText = (() => {
                                if (!titleComp) return ""
                                if (currentLanguage && currentLanguage !== "en") {
                                  const transMap = normalizeTranslationsMap((titleComp as any).translations)
                                  const t = transMap[currentLanguage.toLowerCase()]
                                  if (t && String(t).trim()) return String(t)
                                }
                                return titleComp.generated_content || ""
                              })()
                              const titleKey = `${section.key}:title:1`
                              const isTitleEditing = !!editing[titleKey]
                              const titleEditText = editValues[titleKey] ?? titleText
                              
                              return (
                                <div className="rounded-lg border bg-card p-4 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                      Title <span className="text-gray-400 font-normal">(max 20 chars)</span>
                                    </label>
                                    <span className={`text-xs font-medium ${titleText.length > 20 ? "text-red-500" : titleText.length > 0 ? "text-green-500" : "text-gray-400"}`}>
                                      {titleText.length}/20
                                    </span>
                                  </div>
                                  {isTitleEditing ? (
                                    <div className="space-y-2">
                                      <input
                                        type="text"
                                        maxLength={25}
                                        className="w-full rounded-md border bg-background px-3 py-2 text-sm font-medium"
                                        value={titleEditText}
                                        onChange={(e) => setEditValues(v => ({ ...v, [titleKey]: e.target.value }))}
                                        autoFocus
                                        placeholder="Enter push title..."
                                      />
                                      <div className="flex gap-2">
                                        <Button size="sm" variant="outline" onClick={() => setEditing(v => ({ ...v, [titleKey]: false }))}>
                                          Cancel
                                        </Button>
                                        <Button size="sm" onClick={() => {
                                          if (onUpdateComponent) onUpdateComponent("title", 1, titleEditText, section.key)
                                          setEditing(v => ({ ...v, [titleKey]: false }))
                                        }}>
                                          <Check className="h-3 w-3 mr-1" /> Save
                                        </Button>
                                      </div>
                                    </div>
                                  ) : (
                                    <div 
                                      className={`rounded-md border bg-background px-3 py-2 text-sm cursor-pointer hover:bg-accent transition-colors ${!titleText && 'text-muted-foreground italic'}`}
                                      onClick={() => !isReadOnly && setEditing(v => ({ ...v, [titleKey]: true }))}
                                    >
                                      {titleText || "Click to add title..."}
                                    </div>
                                  )}
                                </div>
                              )
                            })()}
                            
                            {/* Body Editor */}
                            {(() => {
                              const bodyComp = findComponentForSection(components || [], section.key, idx, "body", 1)
                              const bodyText = (() => {
                                if (!bodyComp) return ""
                                if (currentLanguage && currentLanguage !== "en") {
                                  const transMap = normalizeTranslationsMap((bodyComp as any).translations)
                                  const t = transMap[currentLanguage.toLowerCase()]
                                  if (t && String(t).trim()) return String(t)
                                }
                                return bodyComp.generated_content || ""
                              })()
                              const bodyKey = `${section.key}:body:1`
                              const isBodyEditing = !!editing[bodyKey]
                              const bodyEditText = editValues[bodyKey] ?? bodyText
                              
                              return (
                                <div className="rounded-lg border bg-card p-4 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                      Body <span className="text-gray-400 font-normal">(max 100 chars)</span>
                                    </label>
                                    <span className={`text-xs font-medium ${bodyText.length > 100 ? "text-red-500" : bodyText.length > 0 ? "text-green-500" : "text-gray-400"}`}>
                                      {bodyText.length}/100
                                    </span>
                                  </div>
                                  {isBodyEditing ? (
                                    <div className="space-y-2">
                                      <textarea
                                        maxLength={110}
                                        className="w-full rounded-md border bg-background px-3 py-2 text-sm resize-none"
                                        rows={3}
                                        value={bodyEditText}
                                        onChange={(e) => setEditValues(v => ({ ...v, [bodyKey]: e.target.value }))}
                                        autoFocus
                                        placeholder="Enter push body text..."
                                      />
                                      <div className="flex gap-2">
                                        <Button size="sm" variant="outline" onClick={() => setEditing(v => ({ ...v, [bodyKey]: false }))}>
                                          Cancel
                                        </Button>
                                        <Button size="sm" onClick={() => {
                                          if (onUpdateComponent) onUpdateComponent("body", 1, bodyEditText, section.key)
                                          setEditing(v => ({ ...v, [bodyKey]: false }))
                                        }}>
                                          <Check className="h-3 w-3 mr-1" /> Save
                                        </Button>
                                      </div>
                                    </div>
                                  ) : (
                                    <div 
                                      className={`rounded-md border bg-background px-3 py-2 text-sm cursor-pointer hover:bg-accent transition-colors ${!bodyText && 'text-muted-foreground italic'}`}
                                      onClick={() => !isReadOnly && setEditing(v => ({ ...v, [bodyKey]: true }))}
                                    >
                                      {bodyText || "Click to add body text..."}
                                    </div>
                                  )}
                                </div>
                              )
                            })()}
                            
                            {/* Add Component buttons for Push */}
                            {!isReadOnly && (
                              <div className="flex flex-wrap items-center gap-2 pt-2">
                                <span className="text-xs text-muted-foreground">Add optional:</span>
                                {!section.components.includes("cta") && (
                                  <button
                                    type="button"
                                    className="rounded-md border px-2 py-1 text-xs hover:bg-accent"
                                    onClick={() => addComponent(idx, "cta")}
                                  >
                                    + CTA
                                  </button>
                                )}
                                {!section.components.includes("image") && (
                                  <button
                                    type="button"
                                    className="rounded-md border px-2 py-1 text-xs hover:bg-accent"
                                    onClick={() => addComponent(idx, "image")}
                                  >
                                    + Image
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                      <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={({ active, over }) => {
                          if (!active?.id || !over?.id) return
                          const prefix = `comp:${section.key}::`
                          const aId = String(active.id)
                          const oId = String(over.id)
                          if (!aId.startsWith(prefix) || !oId.startsWith(prefix)) return
                          const comps = section.components
                          const ids = comps.map((_, i) => `${prefix}${i}`)
                          const from = ids.indexOf(aId)
                          const to = ids.indexOf(oId)
                          if (from === -1 || to === -1 || from === to) return
                          const reordered = arrayMove(comps, from, to)
                          const next = value.slice()
                          next[idx] = { ...section, components: reordered }
                          onChange(ensureSectionKeys(next))
                        }}
                      >
                        <SortableContext
                          items={section.components.map((_, i) => `comp:${section.key}::${i}`)}
                          strategy={verticalListSortingStrategy}
                        >
                          <div className="mt-3 flex flex-col gap-2">
                            {section.components.length === 0 && (
                              <span className="text-xs text-muted-foreground">No components yet</span>
                            )}
                            {section.components.map((c, compIdx) => {
                              const imgs = (imagesBySection[section.key]?.[compIdx]) || []
                              
                              // Local index: count how many components of this type are in this section up to this point
                              const typeInSectionIdx = section.components.slice(0, compIdx + 1).filter(t => t === c).length;
                              
                              // Find component for THIS section specifically using Type + Section + Local Index
                              const contentObj = findComponentForSection(
                                components || [],
                                section.key,
                                idx,
                                c,
                                typeInSectionIdx
                              )

                              const currentText = (() => {
                                if (!contentObj) return ""
                                if (currentLanguage && currentLanguage !== "en") {
                                  // Re-normalize to be safe, handling both Map and Array formats case-insensitively
                                  const transMap = normalizeTranslationsMap((contentObj as any).translations)
                                  const t = transMap[currentLanguage.toLowerCase()]
                                  // Safe guard: check if translation exists and is not a failure marker
                                  if (t && String(t).trim() && !String(t).includes("__TRANSLATION_FAILED__")) {
                                    return String(t)
                                  }
                                  return `[Missing translation: ${currentLanguage.toUpperCase()}]`
                                }
                                return contentObj.generated_content || ""
                              })()
                              const compKey = `${section.key}:${c}:${typeInSectionIdx}`
                              const isEditing = !!editing[compKey]
                              const editText = editValues[compKey] ?? currentText
                              return (
                                <SortableComponentItem key={`compwrap:${section.key}::${compIdx}`} id={`comp:${section.key}::${compIdx}`}>
                                  {({ attributes, listeners }) => (
                                    <div className="rounded-xl border border-border bg-card p-5 space-y-3 shadow-sm">
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                          <Badge variant="outline" className="text-xs px-2 py-0.5">{c === 'pre_header' ? 'Pre Header' : c.charAt(0).toUpperCase() + c.slice(1)}</Badge>
                                          <span
                                            {...attributes}
                                            {...listeners}
                                            className="cursor-grab active:cursor-grabbing touch-none text-muted-foreground text-xs"
                                          >
                                            ⋮⋮ Drag
                                          </span>
                                        </div>
                                        <button
                                          type="button"
                                          className="rounded border px-2 py-0.5 text-xs hover:bg-accent disabled:opacity-30 disabled:pointer-events-none"
                                          onClick={() => removeComponentAt(idx, compIdx)}
                                          aria-label="Remove component"
                                          disabled={isReadOnly}
                                        >
                                          Remove
                                        </button>
                                      </div>

                                      {c === "image" ? (
                                        imgs.length > 0 ? (
                                          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-md border">
                                            <img src={imgs[0].url} alt={imgs[0].filename} className="h-full w-full object-cover" />
                                            <button
                                              type="button"
                                              className="absolute top-1 right-1 inline-flex h-6 w-6 items-center justify-center rounded bg-black/60 text-white"
                                              onClick={() => removeImageFromComponent(section.key, compIdx, imgs[0].id)}
                                              aria-label="Remove image"
                                            >
                                              ×
                                            </button>
                                          </div>
                                        ) : (
                                          <label
                                            className="flex h-24 items-center justify-center rounded-md border-2 border-dashed text-xs text-muted-foreground cursor-pointer"
                                            onDragOver={(e) => {
                                              e.preventDefault()
                                              e.stopPropagation()
                                            }}
                                            onDrop={(e) => {
                                              e.preventDefault()
                                              e.stopPropagation()
                                              const files = Array.from(e.dataTransfer?.files || []).filter((f) => f.type.startsWith("image/"))
                                              if (files.length) handleUploadToComponent(section.key, compIdx, files)
                                            }}
                                          >
                                            <input
                                              type="file"
                                              accept="image/*"
                                              multiple
                                              className="sr-only"
                                              onChange={(e) => {
                                                const files = e.target.files ? Array.from(e.target.files) : []
                                                if (files.length) handleUploadToComponent(section.key, compIdx, files)
                                              }}
                                            />
                                            Click to upload or drop images here
                                          </label>
                                        )
                                      ) : (
                                        <div className="space-y-3">
                                          {isEditing ? (
                                            <>
                                              <textarea
                                                className="w-full rounded-md border bg-background p-2 text-sm"
                                                rows={6}
                                                value={editText}
                                                onChange={(e) => setEditValues(v => ({ ...v, [compKey]: e.target.value }))}
                                              />
                                              <button
                                                type="button"
                                                className="inline-flex items-center rounded border px-2 py-1 text-xs hover:bg-accent"
                                                onClick={() => {
                                                  setEditing(v => ({ ...v, [compKey]: false }))
                                                  if (onUpdateComponent) {
                                                    onUpdateComponent(c, typeInSectionIdx, editText, section.key)
                                                  }
                                                }}
                                              >
                                                <Check className="h-3.5 w-3.5 mr-1" /> Save
                                              </button>
                                            </>
                                          ) : (
                                            <>{renderPreview(c, typeInSectionIdx, section.key, idx)}</>
                                          )}

                                          {/* Actions toolbar */}
                                          <div className="flex items-center gap-1 pt-1">
                                            <button
                                              type="button"
                                              className="rounded px-2 py-0.5 text-xs hover:bg-accent inline-flex items-center border"
                                              disabled={!!regenBusy[compKey] || (!section.brief && !brief)}
                                              onClick={async () => {
                                                // Use section brief if available, fallback to main brief
                                                const textToUse = section.brief?.trim() || brief
                                                if (!textToUse) return
                                                setRegenBusy(v => ({ ...v, [compKey]: true }))
                                                try {
                                                  const result = await generate({
                                                    project_id: projectId,
                                                    text: textToUse,
                                                    count: 1,
                                                    tone: tone || "professional",
                                                    content_type: "newsletter",
                                                    structure: [{ component: c as any, count: 1 }],
                                                    temperature: 0.8,
                                                    use_few_shot: true,
                                                    use_flash: c === "cta",
                                                  })
                                                  if (result.success && result.data) {
                                                    const val = String(result.data.variations[0][c] || "")
                                                    const finalVal = c === "cta" ? val.toUpperCase() : val
                                                    if (finalVal && onUpdateComponents) {
                                                      // Find this component correctly using section context
                                                      const existingComp = findComponentForSection(
                                                        components || [],
                                                        section.key,
                                                        idx,
                                                        c
                                                      )
                                                      
                                                      // Always retranslate if target languages are set
                                                      if ((targetLanguages || []).length > 0) {
                                                        try {
                                                          // Include section.key in translation key to prevent cross-section contamination
                                                          const translationKey = `${section.key}:${c}${typeInSectionIdx > 1 ? `_${typeInSectionIdx}` : ""}`
                                                          const texts = [{ key: translationKey, content: finalVal }]
                                                          const langs = targetLanguages || []
                                                          const res = await batchTranslate(texts, langs)
                                                          if (res.success && res.data) {
                                                            const newTranslations = res.data[translationKey]
                                                            const merged = (components || []).map((item) => {
                                                              const typeMatch = item.component_type === c
                                                              const sectionMatch = (item as any).section_key === section.key || (item as any).section_order === idx
                                                              if (typeMatch && sectionMatch) {
                                                                return { ...item, generated_content: finalVal, translations: newTranslations }
                                                              }
                                                              return item
                                                            })
                                                            onUpdateComponents(merged as any)
                                                          }
                                                        } catch { }
                                                      } else {
                                                        // No translations to regenerate, just update English content
                                                        const merged = (components || []).map((item) => {
                                                          const typeMatch = item.component_type === c
                                                          const sectionMatch = (item as any).section_key === section.key || (item as any).section_order === idx
                                                          if (typeMatch && sectionMatch) {
                                                            return { ...item, generated_content: finalVal }
                                                          }
                                                          return item
                                                        })
                                                        onUpdateComponents(merged as any)
                                                      }
                                                    }
                                                  }
                                                } finally {
                                                  setRegenBusy(v => ({ ...v, [compKey]: false }))
                                                }
                                              }}
                                            >
                                              {regenBusy[compKey] ? (
                                                <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                                              ) : (
                                                <RefreshCw className="h-3.5 w-3.5 mr-1" />
                                              )}
                                              {contentObj?.generated_content?.trim() ? "Regenerate" : "Generate"}
                                            </button>
                                            <button
                                              type="button"
                                              className="rounded px-2 py-0.5 text-xs hover:bg-accent inline-flex items-center border"
                                              onClick={() => setEditing(v => ({ ...v, [compKey]: !v[compKey] }))}
                                            >
                                              <Edit2 className="h-3 w-3 mr-1" /> Edit
                                            </button>
                                            <button
                                              type="button"
                                              className="rounded px-2 py-0.5 text-xs hover:bg-accent inline-flex items-center border"
                                              onClick={() => handleCopy(currentText)}
                                              disabled={!currentText}
                                            >
                                              <Copy className="h-3 w-3 mr-1" /> Copy
                                            </button>
                                            <button
                                              type="button"
                                              className="rounded px-1.5 py-0.5 text-[10px] hover:bg-accent inline-flex items-center border"
                                              onClick={() => {
                                                const obj = findComponentForSection(
                                                  components || [],
                                                  section.key,
                                                  idx,
                                                  c,
                                                  typeInSectionIdx
                                                )
                                                const en = (obj?.generated_content) || ""
                                                const trAny = (obj as any)?.translations
                                                const trRaw = (trAny && typeof trAny === "object" && !Array.isArray(trAny)) ? trAny : {}
                                                const allowed = new Set((targetLanguages || []).map(l => String(l).toLowerCase()))
                                                const tr = Object.fromEntries(
                                                  Object.entries(trRaw)
                                                    .filter(([k]) => allowed.has(String(k).toLowerCase()))
                                                    .map(([k, v]) => [k, String(v ?? "")])
                                                ) as Record<string, string>
                                                handleCopyHandlebar(`${c}${typeInSectionIdx > 1 ? `_${typeInSectionIdx}` : ""}`, en, tr)
                                              }}
                                              disabled={!((findComponentForSection(components || [], section.key, idx, c, typeInSectionIdx)?.generated_content || "").trim())}
                                            >
                                              <FileCode className="h-3.5 w-3.5 mr-1" /> Handlebar
                                            </button>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </SortableComponentItem>
                              )
                            })}
                          </div>
                        </SortableContext>
                      </DndContext>
                      )}

                      {!isReadOnly && contentType === "newsletter" && (
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          <span className="text-xs text-muted-foreground">Add component:</span>
                          {componentsPalette.map((cp) => (
                            <button
                              key={cp.id}
                              type="button"
                              className="rounded-md border px-2 py-1 text-xs hover:bg-accent"
                              onClick={() => addComponent(idx, cp.id)}
                            >
                              {cp.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </SortableSectionItem>
                  )
                })
              })()}
            </div>
          </SortableContext>
        </DndContext>

        {/* Add Section button - only for newsletters (push notifications are single-section) */}
        {!isReadOnly && contentType === "newsletter" && (
          <div className="mt-3">
            <button
              type="button"
              className="rounded-md border px-3 py-1 text-sm hover:bg-accent"
              onClick={addSection}
            >
              + Add Section
            </button>
          </div>
        )}
      </CardContent>

      <PromptAssistantDialog
        open={optimizationSectionIdx !== null}
        onOpenChange={(open) => !open && setOptimizationSectionIdx(null)}
        originalBrief={optimizationSectionIdx !== null ? value[optimizationSectionIdx]?.brief || value[optimizationSectionIdx]?.name || "" : ""}
        contentType="newsletter"
        tone={tone || "professional"}
        structure={[]} // Section optimization is plain text usually
        onApply={(optimized) => {
          if (optimizationSectionIdx !== null) {
            updateSectionBrief(optimizationSectionIdx, optimized)
            setOptimizationSectionIdx(null)
          }
        }}
      />
    </Card>
  )
}


