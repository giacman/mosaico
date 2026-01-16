"use client"

import { useState, useEffect } from "react"
import { useUser } from "@clerk/nextjs"
import Link from "next/link"
import { ArrowLeft, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { updateProject, type Project } from "@/actions/projects"
import { EmailStructure } from "./email-structure"
import { normalizeComponentList } from "@/lib/section-utils"
import { PromptAssistantDialog } from "../../../_components/prompt-assistant-dialog"
import { getLabelColor } from "../../../_components/create-project-dialog"
import { useProject } from "@/hooks/use-project"
import { useDebounce } from "@/hooks/use-debounce"

interface ProjectEditorProps {
  projectId: number
}

interface UploadedImage {
  id: string
  url: string
  filename: string
  uploading?: boolean
}

const TONES = [
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "enthusiastic", label: "Enthusiastic" },
  { value: "elegant", label: "Elegant" },
  { value: "direct", label: "Direct" }
]

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

export function ProjectEditor({ projectId }: ProjectEditorProps) {
  const { user } = useUser()
  const [mounted, setMounted] = useState(false)

  // Sync mounted state
  useEffect(() => {
    setMounted(true)
  }, [])

  // SWR hook for project data - single source of truth
  const { project: serverProject, isLoading, error, refresh, mutate } = useProject(projectId)

  // Local state for editing (allows optimistic updates)
  const [editedProject, setEditedProject] = useState<Project | null>(null)
  const [images, setImages] = useState<UploadedImage[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [showPromptAssistant, setShowPromptAssistant] = useState(false)
  const [savingStatus, setSavingStatus] = useState(false)

  // Sync local state when server data changes (but preserve local edits)
  useEffect(() => {
    if (serverProject && !editedProject) {
      const normalized = {
        ...serverProject,
        components: normalizeComponentList(serverProject.components)
      }
      setEditedProject(normalized as any)
    }
  }, [serverProject, editedProject])

  // Autosave Logic - Reduced frequency to avoid glitches (30 seconds)
  const debouncedProject = useDebounce(editedProject, 30000)

  // Trigger save when debounced project changes and we have unsaved changes
  useEffect(() => {
    if (debouncedProject && hasChanges && !isSaving) {
      handleSave()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedProject])

  // Loading state
  if (!mounted || isLoading || !editedProject) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-4 pt-0">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-muted-foreground">Loading project...</p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-4 pt-0">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <p className="text-destructive font-medium">Failed to load project</p>
            <p className="text-muted-foreground text-sm mt-2">{error.message}</p>
            <Button variant="outline" className="mt-4" onClick={() => refresh()}>
              Try Again
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Use editedProject for all rendering (local state with optimistic updates)
  const project = editedProject
  const isReadOnly = (project as any).status === "approved"

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const result = await updateProject(project.id, {
        name: project.name,
        brief_text: project.brief_text ?? undefined,
        structure: project.structure,
        tone: project.tone ?? undefined,
        target_languages: project.target_languages,
        labels: project.labels,
        status: (project as any).status
      })

      if (result.success && result.data) {
        const normalized = {
          ...result.data,
          components: normalizeComponentList(result.data.components)
        }
        setEditedProject(normalized as any)
        setHasChanges(false)
        // Update SWR cache immediately with the new data
        mutate(normalized as any, false)
        toast.success("Project saved successfully!")
      } else {
        toast.error(result.error || "Failed to save project")
      }
    } catch (error) {
      console.error("Error saving project:", error)
      toast.error("Failed to save project")
    } finally {
      setIsSaving(false)
    }
  }

  const onChangeStatus = async (value: "in_progress" | "approved") => {
    setSavingStatus(true)
    try {
      const result = await updateProject(project.id, { status: value })
      if (result.success && result.data) {
        setEditedProject(result.data)
        toast.success(`Status updated to ${value.replace("_", " ")}`)
        await refresh() // SWR refresh
      } else {
        toast.error(result.error || "Failed to update status")
      }
    } finally {
      setSavingStatus(false)
    }
  }

  const updateField = <K extends keyof Project>(field: K, value: any, silent: boolean = false) => {
    setEditedProject((prev) => prev ? { ...prev, [field]: value } : prev)
    if (!silent) {
      setHasChanges(true)
    }
  }

  const toggleLanguage = (langCode: string) => {
    const newLanguages = project.target_languages.includes(langCode)
      ? project.target_languages.filter((l) => l !== langCode)
      : [...project.target_languages, langCode]

    updateField("target_languages", newLanguages)
  }

  const toggleLabel = async (label: string) => {
    const currentLabels = project.labels || []
    const newLabels = currentLabels.includes(label)
      ? currentLabels.filter(l => l !== label)
      : [...currentLabels, label]

    // Update local state immediately for UI feedback (optimistic update)
    setEditedProject((prev) => prev ? { ...prev, labels: newLabels } : prev)

    // Auto-save to backend
    try {
      const result = await updateProject(project.id, {
        labels: newLabels
      })

      if (result.success) {
        toast.success(`Label ${currentLabels.includes(label) ? "removed" : "added"}`)
        await refresh() // SWR refresh
      } else {
        // Revert on failure
        setEditedProject((prev) => prev ? { ...prev, labels: currentLabels } : prev)
        toast.error("Failed to update label")
      }
    } catch (error) {
      // Revert on error
      setEditedProject((prev) => prev ? { ...prev, labels: currentLabels } : prev)
      toast.error("Failed to update label")
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-4 pt-0">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
              {isReadOnly && (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/20 dark:text-amber-400">
                  Read-only
                </Badge>
              )}
            </div>
            {hasChanges && (
              <p className="text-sm text-muted-foreground mt-1">Unsaved changes</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Project Status */}
          <div className="flex items-center gap-2">
            <Label className="text-xs text-muted-foreground">Status</Label>
            <Select defaultValue={(project as any).status ?? "in_progress"} onValueChange={onChangeStatus} disabled={savingStatus}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="in_progress">In progress</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            variant="outline"
            onClick={handleSave}
            disabled={isSaving || isReadOnly}
            className={`min-w-[100px] transition-all duration-300 ${!hasChanges && !isSaving ? "text-muted-foreground border-transparent bg-transparent shadow-none" : ""}`}
          >
            <Save className={`mr-2 h-4 w-4 ${isSaving ? "animate-spin" : ""}`} />
            {isSaving ? "Saving..." : hasChanges ? "Save" : "Saved"}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <EmailStructure
          project={project}
          onProjectChange={updateField}
          onStructureChange={(newSections) =>
            updateField("structure", newSections as any)
          }
          onImagesChange={(imgs) => setImages(imgs)}
          userName={user?.fullName || user?.firstName || "Unknown user"}
          isReadOnly={isReadOnly}
        />
      </div>

      {/* Prompt Assistant Dialog */}
      <PromptAssistantDialog
        open={showPromptAssistant}
        onOpenChange={setShowPromptAssistant}
        originalBrief={project.brief_text ?? ""}
        onApply={(optimizedPrompt) => {
          updateField("brief_text", optimizedPrompt)
        }}
      />
    </div>
  )
}
