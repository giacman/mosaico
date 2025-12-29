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

  // ProjectEditor uses SWR to fetch data client-side
  // This ensures fresh data on every mutation
  return <ProjectEditor projectId={projectId} />
}

