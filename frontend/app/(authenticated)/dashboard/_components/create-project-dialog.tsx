"use client"

import { createProject } from "@/actions/projects"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Plus, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import { useNotifications } from "./notifications-provider"

// Pastel color palette for labels
const LABEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  "promo": { bg: "bg-pink-100 dark:bg-pink-950", text: "text-pink-700 dark:text-pink-300", border: "border-pink-200 dark:border-pink-800" },
  "category": { bg: "bg-purple-100 dark:bg-purple-950", text: "text-purple-700 dark:text-purple-300", border: "border-purple-200 dark:border-purple-800" },
  "design": { bg: "bg-blue-100 dark:bg-blue-950", text: "text-blue-700 dark:text-blue-300", border: "border-blue-200 dark:border-blue-800" },
  "october 2025": { bg: "bg-orange-100 dark:bg-orange-950", text: "text-orange-700 dark:text-orange-300", border: "border-orange-200 dark:border-orange-800" },
  "november 2025": { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-300", border: "border-amber-200 dark:border-amber-800" },
  "december 2025": { bg: "bg-emerald-100 dark:bg-emerald-950", text: "text-emerald-700 dark:text-emerald-300", border: "border-emerald-200 dark:border-emerald-800" },
  "default": { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-700 dark:text-gray-300", border: "border-gray-200 dark:border-gray-700" }
}

export function getLabelColor(label: string) {
  return LABEL_COLORS[label.toLowerCase()] || LABEL_COLORS["default"]
}

export function CreateProjectDialog() {
  const router = useRouter()
  const { addNotification } = useNotifications()
  const [open, setOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    labels: [] as string[]
  })
  
  const SUGGESTED_LABELS = [
    "promo",
    "category",
    "design",
    "october 2025",
    "november 2025",
    "december 2025"
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      toast.error("Project name is required")
      return
    }

    setIsCreating(true)

    // Create project with default structure (subject + pre_header)
    const result = await createProject({
      name: formData.name,
      brief_text: undefined,
      structure: [
        { component: "subject", count: 1 },
        { component: "pre_header", count: 1 }
      ],
      tone: "professional",
      target_languages: [],
      labels: formData.labels
    })

    if (result.success && result.data) {
      toast.success("Project created successfully")
      
      // Add persistent notification for team handoff
      const createdBy = result.data.created_by_user_name || "Unknown user"
      addNotification({
        type: "success",
        title: "Project Created",
        message: `Campaign "${result.data.name}" has been created by ${createdBy}. CRM team can now add structure and brief.`
      })
      
      setOpen(false)
      setFormData({ name: "", labels: [] })
      // Navigate to the project editor
      router.push(`/dashboard/projects/${result.data.id}`)
    } else {
      toast.error(result.error || "Failed to create project")
    }

    setIsCreating(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Give your email campaign project a name. You'll add the brief and structure in the editor.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                Project Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g., Spring Collection 2025, Summer Sale Campaign..."
                value={formData.name}
                onChange={e =>
                  setFormData(prev => ({ ...prev, name: e.target.value }))
                }
                disabled={isCreating}
                autoFocus
                autoComplete="off"
                data-1p-ignore
                data-lpignore="true"
                data-form-type="other"
              />
              <p className="text-xs text-muted-foreground">
                You'll add the brief, structure, and other details in the project editor.
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label>Labels (Optional)</Label>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_LABELS.map((label) => {
                    const isSelected = formData.labels.includes(label)
                    return (
                      <Badge
                        key={label}
                        variant={isSelected ? "default" : "outline"}
                        className="cursor-pointer hover:bg-primary/80"
                        onClick={() => {
                          if (isSelected) {
                            setFormData(prev => ({
                              ...prev,
                              labels: prev.labels.filter(l => l !== label)
                            }))
                          } else {
                            setFormData(prev => ({
                              ...prev,
                              labels: [...prev.labels, label]
                            }))
                          }
                        }}
                      >
                        {label}
                      </Badge>
                    )
                  })}
                </div>
                {formData.labels.length > 0 && (
                  <div className="pt-2 border-t">
                    <p className="text-xs font-medium mb-2">Selected:</p>
                    <div className="flex flex-wrap gap-2">
                      {formData.labels.map((label) => {
                        const colors = getLabelColor(label)
                        return (
                          <Badge
                            key={label}
                            variant="secondary"
                            className={`gap-1 ${colors.bg} ${colors.text} ${colors.border} border`}
                          >
                            {label}
                            <X
                              className="h-3 w-3 cursor-pointer"
                              onClick={() => {
                                setFormData(prev => ({
                                  ...prev,
                                  labels: prev.labels.filter(l => l !== label)
                                }))
                              }}
                            />
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
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isCreating}>
              {isCreating ? "Creating..." : "Create Project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

