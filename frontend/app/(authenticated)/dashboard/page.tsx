import { listProjects } from "@/actions/projects"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { FolderKanban, Plus } from "lucide-react"
import Link from "next/link"
import { CreateProjectDialog } from "./_components/create-project-dialog"
import { ProjectCard } from "./_components/project-card"

export default async function DashboardPage() {
  const result = await listProjects()

  if (!result.success) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
        <FolderKanban className="h-12 w-12 text-muted-foreground" />
        <div className="text-center">
          <h2 className="text-2xl font-bold">Failed to Load Projects</h2>
          <p className="text-muted-foreground mt-2">{result.error}</p>
        </div>
      </div>
    )
  }

  const projects = result.data || []

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">
            Create and manage your email campaign projects
          </p>
        </div>
        <CreateProjectDialog />
      </div>

      {projects.length === 0 ? (
        <Card className="flex h-[50vh] flex-col items-center justify-center border-dashed">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <FolderKanban className="h-8 w-8 text-muted-foreground" />
            </div>
            <CardTitle>No Projects Yet</CardTitle>
            <CardDescription className="mx-auto max-w-sm">
              Get started by creating your first email campaign project. Define
              your structure, add images, and let AI generate content.
            </CardDescription>
            <div className="mt-4">
              <CreateProjectDialog />
            </div>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map(project => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  )
}
