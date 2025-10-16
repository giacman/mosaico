import { getProject } from "@/actions/projects"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { ArrowLeft, Sparkles } from "lucide-react"
import Link from "next/link"
import { notFound } from "next/navigation"

export default async function ProjectEditorPage({
  params
}: {
  params: { id: string }
}) {
  const projectId = parseInt(params.id)

  if (isNaN(projectId)) {
    notFound()
  }

  const result = await getProject(projectId)

  if (!result.success || !result.data) {
    notFound()
  }

  const project = result.data

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
          {project.brief_text && (
            <p className="text-muted-foreground mt-1">{project.brief_text}</p>
          )}
        </div>
        <Button>
          <Sparkles className="mr-2 h-4 w-4" />
          Generate Content
        </Button>
      </div>

      {/* Main Content */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Project Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Project Settings</CardTitle>
            <CardDescription>
              Configure your email campaign structure and settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Email Structure</h3>
                <div className="text-sm text-muted-foreground space-y-1">
                  {project.structure.map((item, index) => (
                    <div key={index}>
                      {item.component.replace("_", " ").toUpperCase()}{" "}
                      {item.count > 1 && `(${item.count})`}
                    </div>
                  ))}
                </div>
              </div>

              {project.tone && (
                <div>
                  <h3 className="font-medium mb-2">Tone of Voice</h3>
                  <div className="text-sm text-muted-foreground capitalize">
                    {project.tone}
                  </div>
                </div>
              )}

              {project.target_languages.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Target Languages</h3>
                  <div className="text-sm text-muted-foreground">
                    {project.target_languages.join(", ").toUpperCase()}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Generated Content */}
        <Card>
          <CardHeader>
            <CardTitle>Generated Content</CardTitle>
            <CardDescription>
              AI-generated content for your email campaign
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex h-[200px] items-center justify-center text-center text-muted-foreground">
              <div>
                <p className="mb-2">No content generated yet</p>
                <p className="text-sm">
                  Click &quot;Generate Content&quot; to create your email copy
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Coming Soon Notice */}
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-center">🚧 Project Editor Coming Soon</CardTitle>
          <CardDescription className="text-center">
            This is a placeholder page. The full editor with structure builder,
            image upload, AI generation, and translation features is being built next!
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}

