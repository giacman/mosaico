"use client"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { type Project } from "@/actions/projects"

interface ProjectDetailsCardProps {
  project: Project
  onProjectChange: (field: keyof Project, value: any) => void
}

export function ProjectDetailsCard({
  project,
  onProjectChange
}: ProjectDetailsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Details</CardTitle>
        <CardDescription>
          Basic information about your email campaign
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="project-name">Project Name</Label>
          <Input
            id="project-name"
            value={project.name}
            onChange={(e) => onProjectChange("name", e.target.value)}
            placeholder="e.g., Spring Collection Launch"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="project-brief">Creative Brief</Label>
          <Textarea
            id="project-brief"
            value={project.brief_text ?? ""}
            onChange={(e) =>
              onProjectChange("brief_text", e.target.value || null)
            }
            placeholder="Describe the theme, target audience, key messages..."
            rows={4}
          />
        </div>
      </CardContent>
    </Card>
  )
}
