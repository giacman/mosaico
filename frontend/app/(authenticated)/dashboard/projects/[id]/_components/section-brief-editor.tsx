"use client"

import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Upload, X, AlertCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface SectionBriefEditorProps {
  sectionKey: string
  sectionName: string
  brief: string | null
  imageIds: number[]
  projectImages: Array<{ id: number; url: string; filename: string }>
  globalBrief?: string
  onBriefChange: (brief: string) => void
  onImageIdsChange: (imageIds: number[]) => void
  onUploadClick: () => void
}

export function SectionBriefEditor({
  sectionKey,
  sectionName,
  brief,
  imageIds,
  projectImages,
  globalBrief,
  onBriefChange,
  onImageIdsChange,
  onUploadClick
}: SectionBriefEditorProps) {
  const sectionImages = projectImages.filter(img => imageIds.includes(img.id))
  const hasImages = sectionImages.length > 0
  const hasBrief = brief && brief.trim().length > 0

  return (
    <div className="space-y-3">
      {/* Section Brief */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={`brief-${sectionKey}`} className="text-sm font-medium">
            Section Brief
          </Label>
          {!hasBrief && globalBrief && (
            <span className="text-xs text-muted-foreground">
              Using global brief
            </span>
          )}
        </div>
        <Textarea
          id={`brief-${sectionKey}`}
          placeholder={
            globalBrief 
              ? `Leave empty to use global brief: "${globalBrief.substring(0, 50)}..."`
              : "Describe what to create for this section..."
          }
          value={brief || ""}
          onChange={(e) => onBriefChange(e.target.value)}
          className="min-h-[80px] resize-none"
        />
      </div>

      {/* Section Images */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">
            Section Images
          </Label>
          {!hasImages && (
            <div className="flex items-center gap-1 text-amber-600">
              <AlertCircle className="h-3 w-3" />
              <span className="text-xs">Recommended</span>
            </div>
          )}
        </div>
        
        {hasImages ? (
          <div className="flex flex-wrap gap-2">
            {sectionImages.map((img) => (
              <div key={img.id} className="relative group">
                <img
                  src={img.url}
                  alt={img.filename}
                  className="h-16 w-16 rounded object-cover border"
                />
                <button
                  onClick={() => {
                    onImageIdsChange(imageIds.filter(id => id !== img.id))
                  }}
                  className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onUploadClick}
              className="h-16 w-16"
            >
              <Upload className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onUploadClick}
            className="w-full"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Images for This Section
          </Button>
        )}
      </div>
    </div>
  )
}

