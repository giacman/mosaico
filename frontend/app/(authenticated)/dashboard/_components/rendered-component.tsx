"use client"

import { useState, useEffect } from "react"
import {
  Sparkles,
  Loader2,
  Copy,
  Check,
  Edit2,
  Languages,
  RefreshCw,
  FileCode
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { generateContent } from "@/actions/generate"
import { batchTranslate } from "@/actions/translate"
import { generateHandlebar } from "@/actions/export"
import { useNotifications } from "./notifications-provider"

interface GeneratedComponent {
  key: string
  label: string
  content: string
  sectionName?: string
  editing: boolean
  imageUrl?: string
  isImage?: boolean
}

interface RenderedComponentProps {
  component: GeneratedComponent
  projectId: number
  brief: string
  tone: string
  temperature: number
  targetLanguages: string[]
  translations: Record<string, Record<string, string>>
  onUpdate: (newContent: string) => void
  onSave: (
    updatedComponent: GeneratedComponent,
    newTranslations: Record<string, Record<string, string>>
  ) => void
  readOnly?: boolean
}

export function RenderedComponent({
  component,
  projectId,
  brief,
  tone,
  temperature,
  targetLanguages,
  translations,
  onUpdate,
  onSave,
  readOnly = false
}: RenderedComponentProps) {
  const [isTranslating, setIsTranslating] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(component.content)

  // ... (logic for regenerate, translate, copy, etc. will go here)

  if (component.isImage && component.imageUrl) {
    return (
      <div className="rounded-xl border bg-card p-5 space-y-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs px-2 py-0.5">
            {component.label}
          </Badge>
        </div>
        <div className="relative aspect-[16/9] w-full overflow-hidden rounded-md border">
          <img
            src={component.imageUrl}
            alt={component.label}
            className="h-full w-full object-cover"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-card p-5 space-y-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs px-2 py-0.5">
            {component.label}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {component.content.length} chars
          </span>
        </div>
        <div className="flex items-center gap-1">
          {/* Action buttons will go here */}
        </div>
      </div>

      {editing ? (
        <div className="space-y-3">
          <Textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            rows={8}
            className="font-mono text-base"
            disabled={readOnly}
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => {
                /* save logic */
              }}
              disabled={isTranslating || readOnly}
              className="gap-2"
            >
              <Check className="h-3.5 w-3.5" />
              Save & Retranslate
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setEditing(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <p className="text-base leading-7 whitespace-pre-wrap">
          {component.content}
        </p>
      )}

      {/* Translations will go here */}
    </div>
  )
}

