"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

type ComponentType = "subject" | "pre_header" | "title" | "body" | "cta"

interface StructureComponent {
  component: ComponentType
  count: number
}

interface EmailStructureBuilderProps {
  value: StructureComponent[]
  onChange: (structure: StructureComponent[]) => void
}

const COMPONENT_OPTIONS = [
  { value: "subject" as const, label: "Subject", description: "Email subject line", maxCount: 1 },
  { value: "pre_header" as const, label: "Pre-header", description: "Preview text", maxCount: 1 },
  { value: "title" as const, label: "Title", description: "Main headline", maxCount: 1 },
  { value: "body" as const, label: "Body", description: "Body sections", maxCount: 5 },
  { value: "cta" as const, label: "CTA", description: "Call-to-action buttons", maxCount: 10 },
]

export function EmailStructureBuilder({ value, onChange }: EmailStructureBuilderProps) {
  const [structure, setStructure] = useState<StructureComponent[]>(value)

  const isComponentEnabled = (component: ComponentType) => {
    return structure.some((s) => s.component === component)
  }

  const getComponentCount = (component: ComponentType) => {
    const item = structure.find((s) => s.component === component)
    return item?.count || 1
  }

  const toggleComponent = (component: ComponentType, maxCount: number) => {
    const newStructure = [...structure]
    const index = newStructure.findIndex((s) => s.component === component)

    if (index >= 0) {
      // Remove component
      newStructure.splice(index, 1)
    } else {
      // Add component with default count
      newStructure.push({ component, count: 1 })
    }

    setStructure(newStructure)
    onChange(newStructure)
  }

  const updateComponentCount = (component: ComponentType, count: number, maxCount: number) => {
    const newStructure = structure.map((s) =>
      s.component === component
        ? { ...s, count: Math.max(1, Math.min(count, maxCount)) }
        : s
    )

    setStructure(newStructure)
    onChange(newStructure)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Structure</CardTitle>
        <CardDescription>
          Select the components you want to generate and specify how many of each
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {COMPONENT_OPTIONS.map((option) => {
          const enabled = isComponentEnabled(option.value)
          const count = getComponentCount(option.value)
          const hasMultiple = option.maxCount > 1

          return (
            <div
              key={option.value}
              className="flex items-center justify-between space-x-4 rounded-lg border p-4"
            >
              <div className="flex items-center space-x-4 flex-1">
                <Checkbox
                  id={option.value}
                  checked={enabled}
                  onCheckedChange={() => toggleComponent(option.value, option.maxCount)}
                />
                <div className="flex-1">
                  <Label
                    htmlFor={option.value}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                  >
                    {option.label}
                  </Label>
                  <p className="text-sm text-muted-foreground">{option.description}</p>
                </div>
              </div>

              {hasMultiple && enabled && (
                <div className="flex items-center space-x-2">
                  <Label htmlFor={`${option.value}-count`} className="text-sm text-muted-foreground whitespace-nowrap">
                    Count:
                  </Label>
                  <Input
                    id={`${option.value}-count`}
                    type="number"
                    min={1}
                    max={option.maxCount}
                    value={count}
                    onChange={(e) =>
                      updateComponentCount(
                        option.value,
                        parseInt(e.target.value) || 1,
                        option.maxCount
                      )
                    }
                    className="w-20"
                  />
                </div>
              )}

              {!hasMultiple && enabled && (
                <Badge variant="secondary" className="whitespace-nowrap">
                  1 instance
                </Badge>
              )}
            </div>
          )
        })}

        {structure.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No components selected</p>
            <p className="text-xs mt-1">Select at least one component to generate content</p>
          </div>
        )}

        {structure.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm font-medium mb-2">Selected structure:</p>
            <div className="flex flex-wrap gap-2">
              {structure.map((s) => {
                const option = COMPONENT_OPTIONS.find((o) => o.value === s.component)
                return (
                  <Badge key={s.component} variant="outline">
                    {option?.label} {s.count > 1 && `(${s.count})`}
                  </Badge>
                )
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

