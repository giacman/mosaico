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
import { Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import { useNotifications } from "./notifications-provider"

export function CreateProjectDialog() {
  const router = useRouter()
  const { addNotification } = useNotifications()
  const [open, setOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: ""
  })

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
      target_languages: []
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
      setFormData({ name: "" })
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

