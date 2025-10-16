"use client"

import { FolderKanban, Settings2, User } from "lucide-react"
import * as React from "react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail
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
  const data = {
    user: userData,
    teams: [
      {
        name: "Mosaico",
        logo: User,
        plan: "Workspace"
      }
    ],
    navMain: [
      {
        title: "Projects",
        url: "/dashboard",
        icon: FolderKanban,
        items: []
      },
      {
        title: "Settings",
        url: "#",
        icon: Settings2,
        items: [
          {
            title: "Account",
            url: "/dashboard/account"
          },
          {
            title: "Support",
            url: "/dashboard/support"
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
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
