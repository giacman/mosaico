"use client"

import { deleteProject, type Project } from "@/actions/projects"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import { formatDistanceToNow } from "date-fns"
import { MoreVertical, Pencil, Trash2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"

export function ProjectCard({ project }: { project: Project }) {
  const router = useRouter()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    setIsDeleting(true)
    const result = await deleteProject(project.id)

    if (result.success) {
      toast.success("Project deleted successfully")
      router.refresh()
    } else {
      toast.error(result.error || "Failed to delete project")
    }

    setIsDeleting(false)
    setShowDeleteDialog(false)
  }

  const componentCount = project.structure.reduce(
    (total, item) => total + item.count,
    0
  )

  const languageCount = project.target_languages.length

  return (
    <>
      <Card className="group hover:border-primary transition-colors">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="line-clamp-1">{project.name}</CardTitle>
              <CardDescription className="mt-1">
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
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/dashboard/projects/${project.id}`}>
                    <Pencil className="mr-2 h-4 w-4" />
                    Edit
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => setShowDeleteDialog(true)}
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

