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
import imageCompression from "browser-image-compression"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

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
}: {
  value: Section[]
  onChange: (next: Section[]) => void
  projectId: number
  onImagesChange?: (images: UploadedImage[]) => void
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

  const renderPreview = (type: string) => {
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
        <div className="inline-flex rounded-md border bg-accent/40 px-3 py-1 text-[11px]">
          CTA Button
        </div>
      )
    }
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Structure Input</CardTitle>
        <CardDescription>Arrange sections and components. Mock preview mirrors the output style.</CardDescription>
      </CardHeader>
      <CardContent>

      {/* Fixed header components (visual only) */}
      <div className="mb-4 rounded-md border p-3 bg-muted/30">
        <div className="text-xs font-medium text-muted-foreground">Header (always included)</div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="text-xs px-2 py-0.5">Subject</Badge>
          <Badge variant="outline" className="text-xs px-2 py-0.5">Pre-header</Badge>
        </div>
      </div>

      {/* Sections DnD */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onSectionsDragEnd}>
        <SortableContext items={sectionIds} strategy={verticalListSortingStrategy}>
          <div className="space-y-3">
            {ensureKeys(value).map((section, idx) => (
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
                        return (
                          <SortableComponentItem key={`compwrap:${section.key}::${compIdx}`} id={`comp:${section.key}::${compIdx}`}>
                            {({ attributes, listeners }) => (
                            <div className="rounded-xl border bg-card p-5 space-y-3 shadow-sm">
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
                                  <label className="flex h-24 items-center justify-center rounded-md border-2 border-dashed text-xs text-muted-foreground cursor-pointer">
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
                                  {renderPreview(c)}
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
            ))}
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


