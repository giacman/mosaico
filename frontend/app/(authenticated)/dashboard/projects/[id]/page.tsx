import { getProject } from "@/actions/projects"
import { notFound } from "next/navigation"
import { ProjectEditor } from "./_components/project-editor"

// Force dynamic rendering since this page uses headers() via getProject()
export const dynamic = 'force-dynamic'

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

