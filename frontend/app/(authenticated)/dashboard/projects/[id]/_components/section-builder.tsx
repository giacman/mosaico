"use client"

import React from "react"

type Section = {
  key: string
  name: string
  components: string[]
}

export function SectionBuilder({
  value,
  onChange,
}: {
  value: Section[]
  onChange: (next: Section[]) => void
}) {
  return (
    <div className="rounded-md border p-3 text-sm text-muted-foreground">
      <div className="mb-2 font-medium text-foreground">Email Structure (Sections)</div>
      <div>Coming soon. Current sections: {value?.length ?? 0}</div>
    </div>
  )
}


