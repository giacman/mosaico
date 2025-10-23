"use client"

import { useSearchParams } from "next/navigation"
import { Project } from "../../../../actions/projects"
import { ProjectCard } from "./project-card"
import { Card, CardHeader, CardTitle, CardDescription } from "../../../../components/ui/card"
import { FolderKanban } from "lucide-react"

export function ProjectsGrid({ projects }: { projects: Project[] }) {
  const params = useSearchParams()
  const status = (params.get("status") || "in_progress") as "in_progress" | "approved" | "all"

  const filtered = projects.filter(p => {
    if (status === "all") return true
    const s = (p as any).status || "in_progress"
    return s === status
  })

  if (filtered.length === 0) {
    return (
      <Card className="flex h-[50vh] flex-col items-center justify-center border-dashed">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <FolderKanban className="h-8 w-8 text-muted-foreground" />
          </div>
          <CardTitle>No Projects</CardTitle>
          <CardDescription className="mx-auto max-w-sm">
            There are no projects in this view.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {filtered.map(project => (
        <ProjectCard key={`${project.id}-${project.updated_at}`} project={project} />
      ))}
    </div>
  )
}


