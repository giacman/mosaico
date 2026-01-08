"use client"

import { FolderKanban, Bell, Settings2 } from "lucide-react"
import * as React from "react"
import { useEffect, useState } from "react"
import { listProjects, type Project } from "@/actions/projects"
import { getLabelColor } from "./create-project-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader
} from "@/components/ui/sidebar"
import { NavMain } from "./nav-main"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import { ModeToggle } from "./theme-toggle"

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
  const [newsletterProjects, setNewsletterProjects] = useState<Project[]>([])
  const [pushProjects, setPushProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const [newsletterResult, pushResult] = await Promise.all([
          listProjects("newsletter"),
          listProjects("push_notification")
        ])
        
        if (newsletterResult.success && newsletterResult.data) {
          const sorted = newsletterResult.data
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          setNewsletterProjects(sorted)
        }
        
        if (pushResult.success && pushResult.data) {
          const sorted = pushResult.data
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          setPushProjects(sorted)
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
  
  // Combine all projects for label filtering
  const projects = [...newsletterProjects, ...pushProjects]

  // Extract unique labels from all projects
  const allLabels = Array.from(new Set(projects.flatMap(p => p.labels || []))).sort()

  const [selectedLabels, setSelectedLabels] = useState<string[]>([])

  const toggleFilter = (label: string) => {
    setSelectedLabels(prev =>
      prev.includes(label)
        ? prev.filter(l => l !== label)
        : [...prev, label]
    )
  }

  // Filter projects based on selection
  const filteredNewsletters = selectedLabels.length > 0
    ? newsletterProjects.filter(p => (p.labels || []).some(l => selectedLabels.includes(l)))
    : newsletterProjects
    
  const filteredPush = selectedLabels.length > 0
    ? pushProjects.filter(p => (p.labels || []).some(l => selectedLabels.includes(l)))
    : pushProjects

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
        title: "Newsletter",
        url: "/newsletter",
        icon: FolderKanban,
        items: isLoading
          ? [{ title: "Loading...", url: "#" }]
          : [
            {
              title: "In Progress",
              children: filteredNewsletters
                .filter(p => (p as any).status !== "approved")
                .map(p => ({
                  title: p.name,
                  url: `/newsletter/projects/${p.id}`,
                  labels: p.labels || [] // Passed for the dot logic
                }))
            },
            {
              title: "Approved",
              children: filteredNewsletters
                .filter(p => (p as any).status === "approved")
                .map(p => ({
                  title: p.name,
                  url: `/newsletter/projects/${p.id}`,
                  labels: p.labels || []
                }))
            }
          ]
      },
      {
        title: "Push Notifications",
        url: "/push",
        icon: Bell,
        items: isLoading
          ? [{ title: "Loading...", url: "#" }]
          : [
            {
              title: "In Progress",
              children: filteredPush
                .filter(p => (p as any).status !== "approved")
                .map(p => ({
                  title: p.name,
                  url: `/push/projects/${p.id}`,
                  labels: p.labels || []
                }))
            },
            {
              title: "Approved",
              children: filteredPush
                .filter(p => (p as any).status === "approved")
                .map(p => ({
                  title: p.name,
                  url: `/push/projects/${p.id}`,
                  labels: p.labels || []
                }))
            }
          ]
      }
    ]
  }

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        {/* Filters Section */}
        {!isLoading && allLabels.length > 0 && (
          <div className="px-4 py-2 group-data-[collapsible=icon]:hidden">
            <div className="text-xs font-medium text-muted-foreground mb-2">Filters</div>
            <div className="flex flex-wrap gap-1.5">
              {allLabels.map(label => {
                const colors = getLabelColor(label)
                const isSelected = selectedLabels.includes(label)
                return (
                  <Badge
                    key={label}
                    variant={isSelected ? "default" : "outline"}
                    className={`cursor-pointer px-2 py-0.5 text-[10px] h-5 transition-all
                      ${isSelected
                        ? `${colors.bg} ${colors.text} border-transparent ring-1 ring-primary/20`
                        : "opacity-60 hover:opacity-100 hover:bg-accent"
                      }`}
                    onClick={() => toggleFilter(label)}
                  >
                    {label}
                  </Badge>
                )
              })}
            </div>
            {selectedLabels.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 text-[10px] text-muted-foreground px-0 mt-2 hover:bg-transparent hover:text-foreground"
                onClick={() => setSelectedLabels([])}
              >
                Clear filters
              </Button>
            )}
          </div>
        )}

        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <div className="px-4 py-2 flex items-center justify-between border-t border-sidebar-border/50">
          <span className="text-xs font-medium text-muted-foreground group-data-[collapsible=icon]:hidden">Theme Mode</span>
          <ModeToggle />
        </div>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
