import { listProjects } from "@/actions/projects"
import { CreateProjectDialog } from "../dashboard/_components/create-project-dialog"
import { StatusTabs } from "../dashboard/_components/status-tabs"
import { ProjectsGrid } from "../dashboard/_components/projects-grid"

// Force dynamic rendering since this page uses headers() via listProjects()
export const dynamic = 'force-dynamic'

export default async function PushNotificationsPage() {
  const result = await listProjects("push_notification")
  const projects = result.success && result.data ? result.data : []

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Push Notifications</h1>
          <p className="text-muted-foreground">Create and manage push notification content</p>
        </div>
        <CreateProjectDialog contentType="push_notification" />
      </div>
      <StatusTabs />
      <ProjectsGrid projects={projects} />
    </div>
  )
}
