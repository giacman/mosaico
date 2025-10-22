"use client"

import { deleteProject, duplicateProject, type Project } from "@/actions/projects"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import { formatDistanceToNow } from "date-fns"
import { Copy, MoreVertical, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import { getLabelColor } from "./create-project-dialog"

export function ProjectCard({ project }: { project: Project }) {
  const router = useRouter()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isDuplicating, setIsDuplicating] = useState(false)

  const handleDuplicate = async () => {
    setIsDuplicating(true)
    const result = await duplicateProject(project.id)

    if (result.success && result.data) {
      toast.success(`Project duplicated: ${result.data.name}`)
      router.refresh()
      setTimeout(() => {
        window.location.href = "/dashboard"
      }, 500)
    } else {
      toast.error(result.error || "Failed to duplicate project")
      setIsDuplicating(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    const result = await deleteProject(project.id)

    if (result.success) {
      toast.success("Project deleted successfully")
      setShowDeleteDialog(false)
      // Force a hard refresh to ensure UI updates
      router.refresh()
      // Small delay to ensure the delete completes
      setTimeout(() => {
        window.location.href = "/dashboard"
      }, 500)
    } else {
      toast.error(result.error || "Failed to delete project")
      setIsDeleting(false)
      setShowDeleteDialog(false)
    }
  }

  const componentCount = project.structure.reduce(
    (total, item) => total + item.count,
    0
  )

  const languageCount = project.target_languages.length

  const handleCardClick = () => {
    router.push(`/dashboard/projects/${project.id}`)
  }

  return (
    <>
      <Card 
        className="group hover:border-primary transition-colors cursor-pointer"
        onClick={handleCardClick}
      >
        <CardHeader>
            <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="line-clamp-1">{project.name}</CardTitle>
                {(project as any).status && (
                  <div className="mt-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      (project as any).status === "in_progress"
                        ? "bg-blue-50 text-blue-700 border border-blue-100"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-100"
                    }`}>
                      {(project as any).status.replace("_", " ")}
                    </span>
                  </div>
                )}
              {project.labels && project.labels.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {project.labels.map((label) => {
                    const colors = getLabelColor(label)
                    return (
                      <Badge 
                        key={label} 
                        variant="secondary" 
                        className={`text-xs ${colors.bg} ${colors.text} ${colors.border} border`}
                      >
                        {label}
                      </Badge>
                    )
                  })}
                </div>
              )}
              <CardDescription className="mt-2">
                {project.brief_text ? (
                  <span className="line-clamp-2">{project.brief_text}</span>
                ) : (
                  <span className="text-muted-foreground italic">
                    No brief provided
                  </span>
                )}
              </CardDescription>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDuplicate()
                  }}
                  disabled={isDuplicating}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  {isDuplicating ? "Duplicating..." : "Duplicate"}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowDeleteDialog(true)
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 text-sm text-muted-foreground">
            <div>
              <span className="font-medium text-foreground">
                {componentCount}
              </span>{" "}
              components
            </div>
            {languageCount > 0 && (
              <div>
                <span className="font-medium text-foreground">
                  {languageCount}
                </span>{" "}
                {languageCount === 1 ? "language" : "languages"}
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter className="text-xs text-muted-foreground">
          Updated{" "}
          {formatDistanceToNow(new Date(project.updated_at), {
            addSuffix: true
          })}
          {project.updated_by_user_name && (
            <> by {project.updated_by_user_name}</>
          )}
        </CardFooter>
      </Card>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the project &quot;{project.name}&quot; and
              all its content. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete Project"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

