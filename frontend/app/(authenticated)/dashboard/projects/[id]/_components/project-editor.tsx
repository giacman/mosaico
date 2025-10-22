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
import { EmailStructureBuilderV2 } from "../../../_components/email-structure-builder-v2"
import { ImageUploadManager } from "../../../_components/image-upload-manager"
import { PromptAssistantDialog } from "../../../_components/prompt-assistant-dialog"
import { ContentGenerator } from "../../../_components/content-generator"
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

  const updateField = <K extends keyof Project>(field: K, value: Project[K]) => {
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
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column: Project Settings */}
        <div className="space-y-6">
          {(project as any).status !== "approved" && (
            <>
          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>
                Basic information about your email campaign
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="project-name">Project Name</Label>
                <Input
                  id="project-name"
                  value={project.name}
                  onChange={(e) => updateField("name", e.target.value)}
                  placeholder="e.g., Spring Collection Launch"
                />
              </div>

              <div className="space-y-2">
                <Label>Project Labels</Label>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {["promo", "category", "design", "october 2025", "november 2025", "december 2025"].map((label) => {
                      const isSelected = project.labels?.includes(label) || false
                      const colors = getLabelColor(label)
                      return (
                        <Badge
                          key={label}
                          variant={isSelected ? "default" : "outline"}
                          className={`cursor-pointer hover:opacity-80 transition-opacity ${
                            isSelected ? `${colors.bg} ${colors.text} ${colors.border} border` : ""
                          }`}
                          onClick={() => toggleLabel(label)}
                        >
                          {label}
                        </Badge>
                      )
                    })}
                  </div>
                  {project.labels && project.labels.length > 0 && (
                    <div className="pt-2 border-t">
                      <p className="text-xs font-medium mb-2">Selected:</p>
                      <div className="flex flex-wrap gap-2">
                        {project.labels.map((label) => {
                          const colors = getLabelColor(label)
                          return (
                            <Badge 
                              key={label} 
                              variant="secondary"
                              className={`${colors.bg} ${colors.text} ${colors.border} border`}
                            >
                              {label}
                            </Badge>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Click to add or remove labels for easier project organization.
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="project-brief">Creative Brief</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowPromptAssistant(true)}
                    disabled={!project.brief_text?.trim()}
                    className="gap-2"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Optimize Prompt
                  </Button>
                </div>
                <Textarea
                  id="project-brief"
                  value={project.brief_text ?? ""}
                  onChange={(e) => updateField("brief_text", e.target.value || null)}
                  placeholder="Describe the theme, target audience, key messages... Keep it under 600 characters for best results with images."
                  rows={4}
                />
                <p className="text-xs text-muted-foreground">
                  💡 Use the Prompt Assistant to enhance your brief, or keep under 600 chars when using images
                </p>
              </div>

              {/* Image Upload - Part of the Brief */}
              <div className="space-y-2">
                <Label>Reference Images (Optional)</Label>
                <ImageUploadManager
                  projectId={project.id}
                  value={images}
                  onChange={setImages}
                />
                <p className="text-xs text-muted-foreground">
                  📸 Add images to provide visual context for AI generation
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tone">Tone of Voice</Label>
                <Select
                  value={project.tone ?? "professional"}
                  onValueChange={(value) => updateField("tone", value)}
                >
                  <SelectTrigger id="tone">
                    <SelectValue placeholder="Select tone" />
                  </SelectTrigger>
                  <SelectContent>
                    {TONES.map((tone) => (
                      <SelectItem key={tone.value} value={tone.value}>
                        {tone.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Email Structure */}
          <EmailStructureBuilderV2
            value={project.structure.map((s) => ({
              component: s.component as "subject" | "pre_header" | "title" | "body" | "cta",
              count: s.count
            }))}
            onChange={(structure) => updateField("structure", structure as Array<{component: string; count: number}>)}
          />
            </>
          )}
        </div>

        {/* Right Column: Generated Content Preview */}
        <div className="space-y-6">
          <ContentGenerator
            projectId={project.id}
            brief={project.brief_text ?? ""}
            tone={project.tone ?? "professional"}
            structure={project.structure}
            targetLanguages={project.target_languages}
            onLanguagesChange={(languages) => updateField("target_languages", languages)}
            imageUrls={images.map((img) => img.url)}
            savedComponents={project.components || []}
            userName={user?.fullName || user?.firstName || "Unknown user"}
            readOnly={(project as any).status === "approved"}
          />

        </div>
      </div>

      {/* Prompt Assistant Dialog */}
      <PromptAssistantDialog
        open={showPromptAssistant}
        onOpenChange={setShowPromptAssistant}
        originalBrief={project.brief_text ?? ""}
        contentType="newsletter"
        tone={project.tone ?? "professional"}
        structure={project.structure}
        onApply={(optimizedPrompt) => {
          updateField("brief_text", optimizedPrompt)
        }}
      />
    </div>
  )
}

