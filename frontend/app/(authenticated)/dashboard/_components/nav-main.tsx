"use client"

import { useState, useEffect } from "react"
import { ChevronRight, type LucideIcon } from "lucide-react"
import Link from "next/link"

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from "@/components/ui/collapsible"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar
} from "@/components/ui/sidebar"
import { Badge } from "@/components/ui/badge"
import { getLabelColor } from "./create-project-dialog"

export function NavMain({
  items
}: {
  items: {
    title: string
    url: string
    icon?: LucideIcon
    isActive?: boolean
    items?: {
      title: string
      url: string
      labels?: string[]
    }[]
  }[]
}) {
  const { state } = useSidebar()
  const isCollapsed = state === "collapsed"
  const [mounted, setMounted] = useState(false)

  // Initialize with default closed state
  const defaultOpenState = items.reduce(
    (acc, item) => ({
      ...acc,
      [item.title]: false
    }),
    {} as Record<string, boolean>
  )

  const [openItems, setOpenItems] = useState<Record<string, boolean>>(defaultOpenState)

  // Load from localStorage only on client side after mount
  useEffect(() => {
    setMounted(true)
    
    // Load saved state from localStorage (client-side only)
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("sidebar-open-items")
        if (saved) {
          setOpenItems(JSON.parse(saved))
        }
      } catch (error) {
        console.error("Error loading sidebar state:", error)
      }
    }
  }, [])

  // Save to localStorage whenever openItems changes (client-side only)
  useEffect(() => {
    if (mounted && typeof window !== "undefined") {
      try {
        localStorage.setItem("sidebar-open-items", JSON.stringify(openItems))
      } catch (error) {
        console.error("Error saving sidebar state:", error)
      }
    }
  }, [openItems, mounted])

  // Handle open/close state changes
  const handleOpenChange = (itemTitle: string, isOpen: boolean) => {
    setOpenItems(prev => ({ ...prev, [itemTitle]: isOpen }))
  }

  // Use default state (all closed) until mounted
  const currentOpenState = mounted ? openItems : defaultOpenState

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        {items.map(item => (
          <SidebarMenuItem key={item.title}>
            {isCollapsed && item.items && item.items.length > 0 ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton
                    tooltip={item.title}
                    className="data-[state=open]:bg-accent"
                  >
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="right"
                  align="start"
                  className="w-64 p-2"
                  sideOffset={12}
                >
                  <div className="flex items-center gap-2 px-2 py-1.5 text-sm font-medium">
                    {item.icon && <item.icon className="h-4 w-4" />}
                    <span>{item.title}</span>
                  </div>
                  <DropdownMenuSeparator className="my-1" />
                  {item.items.map(subItem => (
                    <DropdownMenuItem key={subItem.title} asChild>
                      <Link
                        href={subItem.url}
                        className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-3 py-2 text-sm"
                      >
                        <div className="bg-muted-foreground/50 h-1.5 w-1.5 rounded-full flex-shrink-0" />
                        <div className="flex-1 min-w-0 truncate">{subItem.title}</div>
                        {subItem.labels && subItem.labels.length > 0 && (
                          <div className="flex gap-1 flex-shrink-0">
                            {subItem.labels.slice(0, 1).map((label) => {
                              const colors = getLabelColor(label)
                              return (
                                <span 
                                  key={label}
                                  className={`text-[9px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}
                                >
                                  {label}
                                </span>
                              )
                            })}
                            {subItem.labels.length > 1 && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                                +{subItem.labels.length - 1}
                              </span>
                            )}
                          </div>
                        )}
                      </Link>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Collapsible
                asChild
                open={currentOpenState[item.title] ?? false}
                onOpenChange={isOpen => handleOpenChange(item.title, isOpen)}
                className="group/collapsible"
              >
                <div>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton tooltip={item.title}>
                      {item.icon && <item.icon />}
                      <span>{item.title}</span>
                      <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-700 scrollbar-track-transparent">
                      <SidebarMenuSub>
                        {item.items?.map(subItem => (
                          <SidebarMenuSubItem key={subItem.title}>
                            <SidebarMenuSubButton asChild>
                              <a href={subItem.url}>
                                <div className="flex items-center justify-between gap-2 w-full">
                                  <span className="truncate flex-1">{subItem.title}</span>
                                  {subItem.labels && subItem.labels.length > 0 && (
                                    <div className="flex gap-1 flex-shrink-0">
                                      {subItem.labels.slice(0, 1).map((label) => {
                                        const colors = getLabelColor(label)
                                        return (
                                          <span 
                                            key={label}
                                            className={`text-[9px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}
                                          >
                                            {label}
                                          </span>
                                        )
                                      })}
                                      {subItem.labels.length > 1 && (
                                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                                          +{subItem.labels.length - 1}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </a>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            )}
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
