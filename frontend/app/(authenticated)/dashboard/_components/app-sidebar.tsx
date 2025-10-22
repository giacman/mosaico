"use client"

import { FolderKanban, Settings2 } from "lucide-react"
import * as React from "react"
import { useEffect, useState } from "react"
import { listProjects, type Project } from "@/actions/projects"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader
} from "@/components/ui/sidebar"
import { NavMain } from "../_components/nav-main"
import { NavUser } from "../_components/nav-user"
import { TeamSwitcher } from "../_components/team-switcher"

export function AppSidebar({
  userData,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  userData: {
    name: string
    email: string
    avatar: string
    membership: string
  }
}) {
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const result = await listProjects()
        if (result.success && result.data) {
          // Sort by updated_at descending (show all projects)
          const sortedProjects = result.data
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          setProjects(sortedProjects)
        }
      } catch (error) {
        console.error("Error loading projects:", error)
      } finally {
        setIsLoading(false)
      }
    }

    loadProjects()

    // Refresh projects every 30 seconds to catch updates
    const interval = setInterval(loadProjects, 30000)
    return () => clearInterval(interval)
  }, [])

  const data = {
    user: userData,
    teams: [
      {
        name: "Mosaico",
        logo: "🎨",
        plan: "Workspace"
      }
    ],
    navMain: [
      {
        title: "Projects",
        url: "/dashboard",
        icon: FolderKanban,
        items: isLoading 
          ? [{ title: "Loading...", url: "#" }]
          : [
              {
                title: "In Progress",
                children: projects
                  .filter(p => (p as any).status !== "approved")
                  .map(p => ({
                    title: p.name,
                    url: `/dashboard/projects/${p.id}`,
                    labels: p.labels || []
                  }))
              },
              {
                title: "Approved",
                children: projects
                  .filter(p => (p as any).status === "approved")
                  .map(p => ({
                    title: p.name,
                    url: `/dashboard/projects/${p.id}`,
                    labels: p.labels || []
                  }))
              }
            ]
      },
      // Settings group removed (available from user menu)
    ]
  }
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
