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
import { Plus, X, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import { useNotifications } from "./notifications-provider"
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

// Color palette for labels based on their color property
const LABEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  red: { bg: "bg-red-100 dark:bg-red-950", text: "text-red-700 dark:text-red-300", border: "border-red-200 dark:border-red-800" },
  blue: { bg: "bg-blue-100 dark:bg-blue-950", text: "text-blue-700 dark:text-blue-300", border: "border-blue-200 dark:border-blue-800" },
  green: { bg: "bg-green-100 dark:bg-green-950", text: "text-green-700 dark:text-green-300", border: "border-green-200 dark:border-green-800" },
  purple: { bg: "bg-purple-100 dark:bg-purple-950", text: "text-purple-700 dark:text-purple-300", border: "border-purple-200 dark:border-purple-800" },
  orange: { bg: "bg-orange-100 dark:bg-orange-950", text: "text-orange-700 dark:text-orange-300", border: "border-orange-200 dark:border-orange-800" },
  yellow: { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-300", border: "border-amber-200 dark:border-amber-800" },
  pink: { bg: "bg-pink-100 dark:bg-pink-950", text: "text-pink-700 dark:text-pink-300", border: "border-pink-200 dark:border-pink-800" },
  cyan: { bg: "bg-cyan-100 dark:bg-cyan-950", text: "text-cyan-700 dark:text-cyan-300", border: "border-cyan-200 dark:border-cyan-800" },
  gray: { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-700 dark:text-gray-300", border: "border-gray-200 dark:border-gray-700" },
  default: { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-700 dark:text-gray-300", border: "border-gray-200 dark:border-gray-700" }
}

export function getLabelColor(label: string) {
  return LABEL_COLORS[label.toLowerCase()] || LABEL_COLORS["default"]
}

export function CreateProjectDialog() {
  const router = useRouter()
  const { addNotification } = useNotifications()
  const { labels: availableLabels, isLoading: labelsLoading, refresh: refreshLabels } = useLabels()
  const [open, setOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    labels: [] as string[]
  })
  
  // State for creating new labels inline
  const [newLabelName, setNewLabelName] = useState("")
  const [newLabelColor, setNewLabelColor] = useState("gray")
  const [isCreatingLabel, setIsCreatingLabel] = useState(false)
  const [labelPopoverOpen, setLabelPopoverOpen] = useState(false)
  
  // State for deleting labels
  const [labelToDelete, setLabelToDelete] = useState<{ id: number; name: string } | null>(null)
  const [isDeletingLabel, setIsDeletingLabel] = useState(false)
  
  const handleCreateLabel = async () => {
    if (!newLabelName.trim()) return
    
    setIsCreatingLabel(true)
    try {
      const result = await createLabel({ 
        name: newLabelName.trim().toLowerCase(),
        color: newLabelColor
      })
      
      if (result.success) {
        toast.success(`Label "${newLabelName}" created`)
        setNewLabelName("")
        setNewLabelColor("gray")
        setLabelPopoverOpen(false)
        refreshLabels()
      } else {
        toast.error(result.error || "Failed to create label")
      }
    } catch (error) {
      toast.error("Failed to create label")
    } finally {
      setIsCreatingLabel(false)
    }
  }
  
  const handleDeleteLabel = async () => {
    if (!labelToDelete) return
    
    setIsDeletingLabel(true)
    try {
      const result = await deleteLabel(labelToDelete.id)
      
      if (result.success) {
        toast.success(`Label "${labelToDelete.name}" deleted`)
        // Remove from selected labels if it was selected
        setFormData(prev => ({
          ...prev,
          labels: prev.labels.filter(l => l !== labelToDelete.name)
        }))
        refreshLabels()
      } else {
        toast.error(result.error || "Failed to delete label")
      }
    } catch (error) {
      toast.error("Failed to delete label")
    } finally {
      setIsDeletingLabel(false)
      setLabelToDelete(null)
    }
  }

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
    <>
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
              <div className="flex items-center justify-between">
                <Label>Labels (Optional)</Label>
                <Popover open={labelPopoverOpen} onOpenChange={setLabelPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" type="button">
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
                            if (e.key === "Enter") {
                              e.preventDefault()
                              handleCreateLabel()
                            }
                          }}
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Color</Label>
                        <div className="flex flex-wrap gap-1">
                          {Object.keys(LABEL_COLORS).filter(c => c !== "default").map((color) => (
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
                        type="button"
                        size="sm" 
                        className="w-full h-7 text-xs"
                        onClick={handleCreateLabel}
                        disabled={isCreatingLabel || !newLabelName.trim()}
                      >
                        {isCreatingLabel ? <Loader2 className="h-3 w-3 animate-spin" /> : "Create Label"}
                      </Button>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {labelsLoading ? (
                    <span className="text-sm text-muted-foreground">Loading labels...</span>
                  ) : availableLabels.length === 0 ? (
                    <span className="text-sm text-muted-foreground">No labels available. Create one!</span>
                  ) : (
                    availableLabels.map((label) => {
                      const isSelected = formData.labels.includes(label.name)
                      const colors = LABEL_COLORS[label.color] || LABEL_COLORS.default
                      return (
                        <div key={label.id} className="group relative inline-flex">
                          <Badge
                            variant={isSelected ? "default" : "outline"}
                            className={`cursor-pointer hover:opacity-80 transition-opacity pr-6 ${
                              isSelected ? `${colors.bg} ${colors.text} ${colors.border} border` : ""
                            }`}
                            onClick={() => {
                              if (isSelected) {
                                setFormData(prev => ({
                                  ...prev,
                                  labels: prev.labels.filter(l => l !== label.name)
                                }))
                              } else {
                                setFormData(prev => ({
                                  ...prev,
                                  labels: [...prev.labels, label.name]
                                }))
                              }
                            }}
                          >
                            {label.name}
                          </Badge>
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
                        </div>
                      )
                    })
                  )}
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
    
    {/* Delete Label Confirmation Dialog */}
    <AlertDialog open={!!labelToDelete} onOpenChange={(open) => !open && setLabelToDelete(null)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Label</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the label &quot;{labelToDelete?.name}&quot;? 
            This will remove it from all projects that use it. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeletingLabel}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteLabel}
            disabled={isDeletingLabel}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeletingLabel ? "Deleting..." : "Delete Label"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  )
}

