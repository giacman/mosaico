import { listProjects } from "@/actions/projects"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { FolderKanban, Plus } from "lucide-react"
import { CreateProjectDialog } from "./_components/create-project-dialog"
import { StatusTabs } from "./_components/status-tabs"
import { ProjectsGrid } from "./_components/projects-grid"

export const dynamic = "force-dynamic"

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

      {/* Filter Tabs */}
      <StatusTabs />

      <ProjectsGrid projects={projects} />
    </div>
  )
}
