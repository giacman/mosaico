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
import imageCompression from "browser-image-compression"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Edit2, Copy, FileCode, Check } from "lucide-react"
import { Loader2 } from "lucide-react"
import { generateContent } from "@/actions/generate"
import { generateHandlebar } from "@/actions/export"
import { batchTranslate } from "@/actions/translate"

type Section = {
  key: string
  name: string
  components: string[]
}

type UploadedImage = {
  id: string
  url: string
  filename: string
  uploading?: boolean
}

export function SectionBuilder({
  value,
  onChange,
  projectId,
  onImagesChange,
  components,
  brief,
  tone,
  onUpdateComponent,
  currentLanguage = "en",
  targetLanguages = [],
  onUpdateComponents,
}: {
  value: Section[]
  onChange: (next: Section[]) => void
  projectId: number
  onImagesChange?: (images: UploadedImage[]) => void
  components?: Array<{ component_type: string; component_index?: number; generated_content: string; translations?: Record<string,string> }>
  brief?: string
  tone?: string
  onUpdateComponent?: (type: string, index: number, content: string) => void
  currentLanguage?: string
  targetLanguages?: string[]
  onUpdateComponents?: (list: Array<{ component_type: string; component_index?: number; generated_content: string; translations?: Record<string,string> }>) => void
}) {
  const componentsPalette = [
    { id: "title", label: "Title" },
    { id: "body", label: "Body" },
    { id: "cta", label: "CTA" },
    { id: "image", label: "Image" },
  ]

  const ensureKeys = (sections: Section[]): Section[] => {
    return sections.map((s, idx) => ({
      key: s.key || `section_${idx + 1}`,
      name: s.name || `Section ${idx + 1}`,
      components: Array.isArray(s.components) ? s.components : [],
    }))
  }

  // images grouped by section, then by component index
  // imagesBySection[sectionKey][componentIndex] = UploadedImage[]
  const [imagesBySection, setImagesBySection] = useState<Record<string, UploadedImage[][]>>({})
  const storageKey = useMemo(() => `mosaico:imgsec:${projectId}`, [projectId])
  const [loaded, setLoaded] = useState(false)

  // Restore persisted image previews
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed && typeof parsed === "object") {
          setImagesBySection(parsed as Record<string, UploadedImage[][]>)
        }
      }
    } catch {}
    setLoaded(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey])

  // Persist on change + bubble up flattened list (after initial load)
  useEffect(() => {
    if (!loaded) return
    try {
      localStorage.setItem(storageKey, JSON.stringify(imagesBySection))
    } catch {}
    if (onImagesChange) {
      const flat: UploadedImage[] = Object.values(imagesBySection).flat().flat()
      onImagesChange(flat)
    }
  }, [imagesBySection, storageKey, loaded])

  const addSection = () => {
    const next: Section[] = ensureKeys([
      ...value,
      {
        key: "",
        name: "",
        components: [],
      },
    ])
    onChange(next)
  }

  const renameSection = (idx: number, name: string) => {
    const next = value.slice()
    next[idx] = { ...next[idx], name }
    onChange(ensureKeys(next))
  }

  const removeSection = (idx: number) => {
    const next = value.slice()
    const removed = next.splice(idx, 1)[0]
    onChange(ensureKeys(next))
    if (removed) {
      setImagesBySection((prev) => {
        const copy = { ...prev }
        delete copy[removed.key]
        return copy
      })
    }
  }

  const addComponent = (idx: number, comp: string) => {
    if (!comp) return
    const next = value.slice()
    const section = next[idx]
    next[idx] = { ...section, components: [...section.components, comp] }
    onChange(ensureKeys(next))
    const sKey = ensureKeys(next)[idx].key
    setImagesBySection((prev) => ({
      ...prev,
      [sKey]: [...(prev[sKey] || []), []],
    }))
  }

  const removeComponentAt = (idx: number, compIdx: number) => {
    const next = value.slice()
    const section = next[idx]
    const comps = section.components.slice()
    comps.splice(compIdx, 1)
    next[idx] = { ...section, components: comps }
    onChange(ensureKeys(next))
    const sKey = ensureKeys(next)[idx].key
    setImagesBySection((prev) => {
      const arr = (prev[sKey] || []).slice()
      arr.splice(compIdx, 1)
      return { ...prev, [sKey]: arr }
    })
  }

  // ---- Drag and Drop (Sections) ----
  const sectionIds = useMemo(() => ensureKeys(value).map((s) => `section:${s.key}`), [value])
  const sensors = useSensors(useSensor(PointerSensor))

  const onSectionsDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!active?.id || !over?.id) return
    const from = sectionIds.indexOf(String(active.id))
    const to = sectionIds.indexOf(String(over.id))
    if (from === -1 || to === -1 || from === to) return
    const next = arrayMove(ensureKeys(value), from, to)
    onChange(next)
  }

  function SortableSectionItem({ id, children }: { id: string; children: React.ReactNode }) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id })
    const style: React.CSSProperties = {
      transform: CSS.Transform.toString(transform),
      transition,
    }
    return (
      <div ref={setNodeRef} style={style} className="rounded-md border p-3 bg-card/50">
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing touch-none -mt-1 -mb-1 mb-2 text-xs text-muted-foreground"
        >
          Drag to reorder
        </div>
        {children}
      </div>
    )
  }

  function SortableComponentItem({ id, children }: { id: string; children: (p: { attributes: any; listeners: any }) => React.ReactNode }) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id })
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
    setImagesBySection((prev) => {
      const list = (prev[sectionKey] || []).slice()
      const current = (list[compIdx] || [])
      const temps: UploadedImage[] = files.map((f) => ({
        id: `temp-${Math.random().toString(36).slice(2)}`,
        url: URL.createObjectURL(f),
        filename: f.name,
        uploading: true,
      }))
      list[compIdx] = [...current, ...temps]
      return { ...prev, [sectionKey]: list }
    })

    for (let i = 0; i < files.length; i++) {
      const original = files[i]
      try {
        const compressed = await compressImage(original)
        const res = await uploadImage(projectId, compressed)
        if (!res.success || !res.data) throw new Error(res.error || "Upload failed")
        const uploaded: UploadedImage = {
          id: String(res.data.id),
          url: res.data.gcs_public_url || res.data.gcs_path,
          filename: res.data.filename,
        }
        setImagesBySection((prev) => {
          const list = (prev[sectionKey] || []).slice()
          const current = (list[compIdx] || []).map((img) => (img.uploading ? uploaded : img))
          list[compIdx] = current
          return { ...prev, [sectionKey]: list }
        })
      } catch (e) {
        setImagesBySection((prev) => {
          const list = (prev[sectionKey] || []).slice()
          const current = (list[compIdx] || []).filter((img) => !img.uploading)
          list[compIdx] = current
          return { ...prev, [sectionKey]: list }
        })
      }
    }
  }

  const removeImageFromComponent = (sectionKey: string, compIdx: number, imageId: string) => {
    setImagesBySection((prev) => {
      const list = (prev[sectionKey] || []).slice()
      const current = (list[compIdx] || []).filter((img) => img.id !== imageId)
      list[compIdx] = current
      return { ...prev, [sectionKey]: list }
    })
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

  const renderPreview = (type: string, displayIndex: number) => {
    // Try to resolve generated or translated content for this component type/index
    const idx = displayIndex <= 0 ? 1 : displayIndex
    const found = components?.find(
      (c) => c.component_type === type && (c.component_index || 1) === idx
    )

    const text = (() => {
      if (!found) return ""
      if (currentLanguage && currentLanguage !== "en") {
        const t = found.translations?.[currentLanguage]
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

  const handleCopy = async (text: string) => {
    try { await navigator.clipboard.writeText(text) } catch {}
  }

  const handleCopyHandlebar = async (
    key: string,
    englishFallback: string,
    translations?: Record<string, string>
  ) => {
    try {
      const res = await generateHandlebar({
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
    <Card className="mx-auto max-w-[840px] bg-white shadow-xl ring-1 ring-black/5">
      <CardHeader>
        <CardTitle>Email Structure Input</CardTitle>
        <CardDescription>Arrange sections and components. Mock preview mirrors the output style.</CardDescription>
      </CardHeader>
      <CardContent className="px-6 sm:px-8 md:px-10 py-8">

      {/* Fixed header components (visual only) */}
      <div className="mb-4 rounded-md border p-3 bg-muted/30">
        <div className="text-xs font-medium text-muted-foreground">Header (always included)</div>
        <div className="mt-3 space-y-3">
          {(() => {
            const headerItems: Array<{ label: string; type: "subject" | "pre_header" }> = [
              { label: "Subject", type: "subject" },
              { label: "Pre-header", type: "pre_header" },
            ]
            return headerItems.map(({ label, type }) => {
              const displayIndex = 1
              const found = components?.find(
                (c) => c.component_type === type && (c.component_index || 1) === 1
              )
              const currentText = found?.generated_content || ""
              const compKey = `header:${type}:${displayIndex}`
              const isEditing = !!editing[compKey]
              const editText = editValues[compKey] ?? currentText
              return (
                <div key={type} className="rounded-xl border bg-card p-4 space-y-2 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs px-2 py-0.5">{label}</Badge>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                        disabled={!!regenBusy[compKey] || !brief}
                        onClick={async () => {
                          if (!brief) return
                          setRegenBusy(v => ({ ...v, [compKey]: true }))
                          try {
                            const result = await generateContent({
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
                              if (val) onUpdateComponent && onUpdateComponent(type, 1, val)
                              if ((targetLanguages || []).length > 0 && val) {
                                try {
                                  const texts = [{ key: type, content: val }]
                                  const langs = targetLanguages || []
                                  const res = await batchTranslate(texts, langs)
                                  if (res.success && res.data && onUpdateComponents) {
                                    const key = type
                                    const t = (res.data[key] || {}) as Record<string, string>
                                    const merged = (components || []).map((c) => {
                                      if (c.component_type === type && (c.component_index || 1) === 1) {
                                        return { ...c, generated_content: val, translations: { ...(c.translations || {}), ...t } }
                                      }
                                      return c
                                    })
                                    onUpdateComponents(merged as any)
                                  }
                                } catch {}
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
                        Regenerate
                      </button>
                      <button
                        type="button"
                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                        onClick={() => setEditing(v => ({ ...v, [compKey]: !v[compKey] }))}
                      >
                        <Edit2 className="h-3.5 w-3.5 mr-1" /> Edit
                      </button>
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
                        disabled={!currentText && !(found && (found as any).translations && (found as any).translations[currentLanguage || ""]) }
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

                  {isEditing ? (
                    <>
                      <textarea
                        className="w-full rounded-md border bg-background p-2 text-sm"
                        rows={4}
                        value={editText}
                        onChange={(e) => setEditValues(v => ({ ...v, [compKey]: e.target.value }))}
                      />
                      <button
                        type="button"
                        className="inline-flex items-center rounded border px-2 py-1 text-xs hover:bg-accent"
                        onClick={() => {
                          setEditing(v => ({ ...v, [compKey]: false }))
                          onUpdateComponent && onUpdateComponent(type, 1, editText)
                        }}
                      >
                        <Check className="h-3.5 w-3.5 mr-1" /> Save
                      </button>
                    </>
                  ) : (
                    <div>{renderPreview(type, 1)}</div>
                  )}
                </div>
              )
            })
          })()}
        </div>
      </div>

      {/* Sections DnD */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onSectionsDragEnd}>
        <SortableContext items={sectionIds} strategy={verticalListSortingStrategy}>
          <div className="space-y-3">
            {(() => {
              // Global per-type counters across ALL sections to map to generated components correctly
              const globalTypeCounters: Record<string, number> = {}
              return ensureKeys(value).map((section, idx) => (
                <SortableSectionItem key={`section:${section.key}`} id={`section:${section.key}`}>
                  <div className="flex items-center gap-2">
                    <input
                      value={section.name}
                      onChange={(e) => renameSection(idx, e.target.value)}
                      placeholder={`Section ${idx + 1} name`}
                      className="w-full rounded-md border bg-background px-2 py-1 text-sm"
                    />
                    <button
                      type="button"
                      className="rounded-md border px-2 py-1 text-xs hover:bg-accent"
                      onClick={() => removeSection(idx)}
                      aria-label="Remove section"
                    >
                      Remove
                    </button>
                  </div>

                  {/* Components DnD within section (no cross-section moves) */}
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
                      // Reorder images slots accordingly
                      setImagesBySection((prev) => {
                        const arr = (prev[section.key] || []).slice()
                        const re = arrayMove(arr, from, to)
                        return { ...prev, [section.key]: re }
                      })
                      onChange(ensureKeys(next))
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
                          // Global display index: increment per type across all sections
                          const displayIndex = (globalTypeCounters[c] = (globalTypeCounters[c] || 0) + 1)
                          const contentObj = components?.find(x => x.component_type === c && (x.component_index || 1) === displayIndex)
                          const currentText = (() => {
                            if (!contentObj) return ""
                            if (currentLanguage && currentLanguage !== "en") {
                              const t = (contentObj as any).translations?.[currentLanguage]
                              if (t && String(t).trim()) return String(t)
                            }
                            return contentObj.generated_content || ""
                          })()
                          const compKey = `${section.key}:${c}:${displayIndex}`
                          const isEditing = !!editing[compKey]
                          const editText = editValues[compKey] ?? currentText
                          return (
                            <SortableComponentItem key={`compwrap:${section.key}::${compIdx}`} id={`comp:${section.key}::${compIdx}`}>
                              {({ attributes, listeners }) => (
                              <div className="rounded-xl border bg-white p-5 space-y-3 shadow-sm">
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
                                    className="rounded border px-2 py-0.5 text-xs hover:bg-accent"
                                    onClick={() => removeComponentAt(idx, compIdx)}
                                    aria-label="Remove component"
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
                                            onUpdateComponent && onUpdateComponent(c, displayIndex, editText)
                                          }}
                                        >
                                          <Check className="h-3.5 w-3.5 mr-1" /> Save
                                        </button>
                                      </>
                                    ) : (
                                      <>{renderPreview(c, displayIndex)}</>
                                    )}

                                    {/* Actions toolbar */}
                                    <div className="flex items-center gap-1 pt-1">
                                      <button
                                        type="button"
                                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                                        disabled={!!regenBusy[compKey]}
                                        onClick={async () => {
                                          if (!brief) return
                                          setRegenBusy(v => ({ ...v, [compKey]: true }))
                                          try {
                                            const result = await generateContent({
                                              text: brief,
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
                                              if (finalVal) onUpdateComponent && onUpdateComponent(c, displayIndex, finalVal)
                                              if ((targetLanguages || []).length > 0 && finalVal && onUpdateComponents) {
                                                try {
                                                  const texts = [{ key: `${c}${displayIndex > 1 ? `_${displayIndex}` : ""}`, content: finalVal }]
                                                  const langs = targetLanguages || []
                                                  const res = await batchTranslate(texts, langs)
                                                  if (res.success && res.data) {
                                                    const key = `${c}${displayIndex > 1 ? `_${displayIndex}` : ""}`
                                                    const rawT = (res.data[key] || {}) as Record<string, string>
                                                    const t = c === "cta"
                                                      ? Object.fromEntries(Object.entries(rawT).map(([k,v]) => [k, String(v || "").toUpperCase()])) as Record<string,string>
                                                      : rawT
                                                    const merged = (components || []).map((item) => {
                                                      if (item.component_type === c && (item.component_index || 1) === displayIndex) {
                                                        return { ...item, generated_content: finalVal, translations: { ...(item.translations || {}), ...t } }
                                                      }
                                                      return item
                                                    })
                                                    onUpdateComponents(merged as any)
                                                  }
                                                } catch {}
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
                                        Regenerate
                                      </button>
                                      <button
                                        type="button"
                                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                                        onClick={() => setEditing(v => ({ ...v, [compKey]: !v[compKey] }))}
                                      >
                                        <Edit2 className="h-3.5 w-3.5 mr-1" /> Edit
                                      </button>
                                      <button
                                        type="button"
                                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                                        onClick={() => handleCopy(currentText)}
                                        disabled={!currentText}
                                      >
                                        <Copy className="h-3.5 w-3.5 mr-1" /> Copy
                                      </button>
                                      <button
                                        type="button"
                                        className="rounded px-2 py-1 text-xs hover:bg-accent inline-flex items-center border"
                                        onClick={() => {
                                          const obj = components?.find(x => x.component_type === c && (x.component_index || 1) === displayIndex)
                                          const en = (obj?.generated_content) || ""
                                          const trAny = (obj as any)?.translations
                                          const trRaw = (trAny && typeof trAny === "object" && !Array.isArray(trAny)) ? trAny : {}
                                          const allowed = new Set((targetLanguages || []).map(l => String(l).toLowerCase()))
                                          const tr = Object.fromEntries(
                                            Object.entries(trRaw)
                                              .filter(([k]) => allowed.has(String(k).toLowerCase()))
                                              .map(([k, v]) => [k, String(v ?? "")])
                                          ) as Record<string, string>
                                          handleCopyHandlebar(`${c}${displayIndex > 1 ? `_${displayIndex}` : ""}`, en, tr)
                                        }}
                                        disabled={!((components?.find(x => x.component_type === c && (x.component_index || 1) === displayIndex)?.generated_content || "").trim())}
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
                </SortableSectionItem>
              ))
            })()}
          </div>
        </SortableContext>
      </DndContext>

      <div className="mt-3">
        <button
          type="button"
          className="rounded-md border px-3 py-1 text-sm hover:bg-accent"
          onClick={addSection}
        >
          + Add Section
        </button>
      </div>
      </CardContent>
    </Card>
  )
}


