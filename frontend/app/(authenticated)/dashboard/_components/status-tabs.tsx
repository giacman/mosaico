"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"

export function StatusTabs() {
  const searchParams = useSearchParams()
  const current = searchParams.get("status") || "in_progress"

  const tabs = [
    { key: "in_progress", label: "In Progress" },
    { key: "approved", label: "Approved" },
    { key: "all", label: "All" }
  ]

  return (
    <div className="flex items-center gap-2">
      {tabs.map(tab => (
        <Link key={tab.key} href={`/newsletter?status=${tab.key}`}>
          <Button variant={current === tab.key ? "default" : "outline"} size="sm">
            {tab.label}
          </Button>
        </Link>
      ))}
    </div>
  )
}


