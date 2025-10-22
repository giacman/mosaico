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
    url?: string
    isHeading?: boolean
    separator?: boolean
    indent?: boolean
      labels?: string[]
    children?: {
      title: string
      url: string
      labels?: string[]
    }[]
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

  // Sub-group open state (e.g., In Progress / Approved)
  const defaultSubOpenState = items.reduce((acc, item) => {
    const sub = item.items || []
    for (const si of sub) {
      // Default: keep "In Progress" open
      acc[si.title] = si.title.toLowerCase().includes("in progress")
    }
    return acc
  }, {} as Record<string, boolean>)
  const [openSubItems, setOpenSubItems] = useState<Record<string, boolean>>(defaultSubOpenState)

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
        const savedSub = localStorage.getItem("sidebar-open-subitems")
        if (savedSub) {
          setOpenSubItems(JSON.parse(savedSub))
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
        localStorage.setItem("sidebar-open-subitems", JSON.stringify(openSubItems))
      } catch (error) {
        console.error("Error saving sidebar state:", error)
      }
    }
  }, [openItems, openSubItems, mounted])

  // Handle open/close state changes
  const handleOpenChange = (itemTitle: string, isOpen: boolean) => {
    setOpenItems(prev => ({ ...prev, [itemTitle]: isOpen }))
  }

  // Use default state (all closed) until mounted
  const currentOpenState = mounted ? openItems : defaultOpenState
  const currentSubOpenState = mounted ? openSubItems : defaultSubOpenState

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
                  {item.items.map((subItem, idx) => (
                    subItem.isHeading ? (
                      <div key={`heading-${idx}`} className="px-3 py-1.5 text-xs font-semibold text-muted-foreground">
                        {subItem.title}
                      </div>
                    ) : subItem.separator ? (
                      <DropdownMenuSeparator key={`sep-${idx}`} className="my-1" />
                    ) : (
                      <DropdownMenuItem key={subItem.title} asChild>
                        <Link
                          href={subItem.url || "#"}
                          className={`hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-3 py-2 text-sm ${subItem.indent ? 'pl-4' : ''}`}
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
                    )
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
                        {item.items?.map((subItem, idx) => (
                          subItem.separator ? (
                            <div key={`sep-${idx}`} className="h-px bg-border mx-3 my-1" />
                          ) : subItem.children && subItem.children.length > 0 ? (
                            <SidebarMenuSubItem key={subItem.title}>
                              <Collapsible
                                open={currentSubOpenState[subItem.title] ?? false}
                                onOpenChange={(isOpen) => setOpenSubItems(prev => ({ ...prev, [subItem.title]: isOpen }))}
                              >
                                <CollapsibleTrigger asChild>
                                  <div className="px-3 py-1.5 text-[12px] font-medium text-muted-foreground cursor-pointer select-none flex items-center gap-2">
                                    <ChevronRight className="h-3 w-3 transition-transform data-[state=open]:rotate-90" />
                                    {subItem.title}
                                  </div>
                                </CollapsibleTrigger>
                                <CollapsibleContent>
                                  <div className="ml-3 border-l pl-3 space-y-1">
                                    {subItem.children.map(child => (
                                      <SidebarMenuSubButton key={child.title} asChild>
                                        <a href={child.url}>
                                          <div className="flex items-center justify-between gap-2 w-full">
                                            <span className="truncate flex-1">{child.title}</span>
                                            {child.labels && child.labels.length > 0 && (
                                              <div className="flex gap-1 flex-shrink-0">
                                                {child.labels.slice(0, 1).map((label) => {
                                                  const colors = getLabelColor(label)
                                                  return (
                                                    <span key={label} className={`text-[9px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}>{label}</span>
                                                  )
                                                })}
                                              </div>
                                            )}
                                          </div>
                                        </a>
                                      </SidebarMenuSubButton>
                                    ))}
                                  </div>
                                </CollapsibleContent>
                              </Collapsible>
                            </SidebarMenuSubItem>
                          ) : (
                            <SidebarMenuSubItem key={`link-${idx}`}>
                              <SidebarMenuSubButton asChild>
                                <a href={subItem.url || "#"}>
                                  <span className="truncate flex-1">{subItem.title}</span>
                                </a>
                              </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                          )
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
