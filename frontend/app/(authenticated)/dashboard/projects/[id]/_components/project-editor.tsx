"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@clerk/nextjs"
import Link from "next/link"
import { ArrowLeft, Save, Sparkles } from "lucide-react"
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
import { EmailStructure } from "./email-structure" // Import the new component
import { PromptAssistantDialog } from "../../../_components/prompt-assistant-dialog"
import { getLabelColor } from "../../../_components/create-project-dialog"

interface ProjectEditorProps {
  initialProject: Project
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

export function ProjectEditor({ initialProject }: ProjectEditorProps) {
  const router = useRouter()
  const { user } = useUser()
  const [mounted, setMounted] = useState(false)
  const [project, setProject] = useState(initialProject)
  const [images, setImages] = useState<UploadedImage[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [showPromptAssistant, setShowPromptAssistant] = useState(false)
  const [savingStatus, setSavingStatus] = useState(false)

  // Fix hydration by only rendering after mount
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    // Show loading skeleton while hydrating
    return (
      <div className="flex flex-1 flex-col gap-6 p-4 pt-0">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            <div className="h-10 w-10 rounded-md bg-muted animate-pulse" />
            <div className="space-y-2">
              <div className="h-8 w-64 rounded bg-muted animate-pulse" />
              <div className="h-4 w-32 rounded bg-muted animate-pulse" />
            </div>
          </div>
          <div className="flex gap-2">
            <div className="h-10 w-24 rounded-md bg-muted animate-pulse" />
            <div className="h-10 w-40 rounded-md bg-muted animate-pulse" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="h-96 rounded-lg bg-muted animate-pulse" />
            <div className="h-96 rounded-lg bg-muted animate-pulse" />
          </div>
          <div className="h-96 rounded-lg bg-muted animate-pulse" />
        </div>
      </div>
    )
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const result = await updateProject(project.id, {
        name: project.name,
        brief_text: project.brief_text ?? undefined,
        structure: project.structure,
        tone: project.tone ?? undefined,
        target_languages: project.target_languages,
        labels: project.labels
      })

      if (result.success) {
        toast.success("Project saved successfully!")
        setHasChanges(false)
        router.refresh()
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
        setProject(result.data)
        toast.success(`Status updated to ${value.replace("_", " ")}`)
        router.refresh()
      } else {
        toast.error(result.error || "Failed to update status")
      }
    } finally {
      setSavingStatus(false)
    }
  }

  const updateField = <K extends keyof Project>(field: K, value: any) => {
    setProject((prev) => ({ ...prev, [field]: value }))
    setHasChanges(true)
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
    
    // Update local state immediately for UI feedback
    setProject((prev) => ({ ...prev, labels: newLabels }))
    
    // Auto-save to backend
    try {
      const result = await updateProject(project.id, {
        labels: newLabels
      })

      if (result.success) {
        toast.success(`Label ${currentLabels.includes(label) ? "removed" : "added"}`)
        router.refresh()
      } else {
        // Revert on failure
        setProject((prev) => ({ ...prev, labels: currentLabels }))
        toast.error("Failed to update label")
      }
    } catch (error) {
      // Revert on error
      setProject((prev) => ({ ...prev, labels: currentLabels }))
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
            <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
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
            disabled={!hasChanges || isSaving}
          >
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? "Saving..." : "Save"}
          </Button>
          <Button disabled>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Content
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {/* This is where the new, single-column layout will go. */}
        <EmailStructure
          project={project}
          onProjectChange={updateField}
          onStructureChange={(newSections) =>
            updateField("structure", newSections as any)
          }
          onImagesChange={(imgs) => setImages(imgs)}
          userName={user?.fullName || user?.firstName || "Unknown user"}
        />
      </div>

      {/* Prompt Assistant Dialog */}
      <PromptAssistantDialog
        open={showPromptAssistant}
        onOpenChange={setShowPromptAssistant}
        originalBrief={project.brief_text ?? ""}
        contentType="newsletter"
        tone={project.tone ?? "professional"}
        structure={project.structure as any}
        onApply={(optimizedPrompt) => {
          updateField("brief_text", optimizedPrompt)
        }}
      />
    </div>
  )
}

