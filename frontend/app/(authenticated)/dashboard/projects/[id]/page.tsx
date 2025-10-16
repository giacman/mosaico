import { getProject } from "@/actions/projects"
import { notFound } from "next/navigation"
import { ProjectEditor } from "./_components/project-editor"

export default async function ProjectEditorPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const projectId = parseInt(id)

  if (isNaN(projectId)) {
    notFound()
  }

  const result = await getProject(projectId)

  if (!result.success || !result.data) {
    notFound()
  }

  return <ProjectEditor initialProject={result.data} />
}

