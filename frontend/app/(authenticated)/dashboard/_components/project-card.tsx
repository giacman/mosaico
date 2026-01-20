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
import { Copy, MoreVertical, Trash2, ImageIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import Image from "next/image"
import { getFlagUrlForLanguage } from "@/lib/languages"

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
}


interface ProjectCardProps {
  project: Project
  labelColorMap?: Record<string, string>
}

export function ProjectCard({ project, labelColorMap = {} }: ProjectCardProps) {
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

  const componentCount = Array.isArray(project.structure)
    ? project.structure.reduce((total, item: any) => {
        // New sections-based structure
        if (Array.isArray(item?.components)) {
          return total + item.components.length
        }
        // Legacy structure: { component, count }
        const count = Number(item?.count ?? 0)
        return total + (Number.isFinite(count) ? count : 0)
      }, 0)
    : 0

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
                    const colorName = labelColorMap[label] || "gray"
                    const colors = LABEL_COLORS[colorName] || LABEL_COLORS.gray
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
        
        {/* Image Preview Section */}
        {project.images && project.images.length > 0 && (
          <div className="px-6 pb-4">
            <div className="flex gap-2 items-center">
              {project.images.slice(0, 3).map((image, idx) => (
                <div
                  key={image.id}
                  className="relative w-16 h-16 rounded-md overflow-hidden border border-border bg-muted"
                  onClick={(e) => e.stopPropagation()}
                >
                  {image.gcs_public_url ? (
                    <Image
                      src={image.gcs_public_url}
                      alt={image.filename}
                      fill
                      className="object-cover"
                      sizes="64px"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ImageIcon className="w-6 h-6 text-muted-foreground" />
                    </div>
                  )}
                </div>
              ))}
              {project.images.length > 3 && (
                <div className="flex items-center justify-center w-16 h-16 rounded-md border border-dashed border-border bg-muted/50">
                  <span className="text-xs font-medium text-muted-foreground">
                    +{project.images.length - 3}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <CardContent>
          <div className="space-y-3">
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
            
            {/* Language Flags */}
            {project.target_languages && project.target_languages.length > 0 && (
              <div className="flex gap-1.5 items-center">
                {project.target_languages.map((lang) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img 
                    key={lang}
                    src={getFlagUrlForLanguage(lang, 20)}
                    alt={lang.toUpperCase()}
                    width={20}
                    height={15}
                    title={lang.toUpperCase()}
                  />
                ))}
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

