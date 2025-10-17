"use client"

import { useState, useCallback } from "react"
import { Upload, X, Image as ImageIcon, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { uploadImage } from "@/actions/upload"

interface UploadedImage {
  id: string
  url: string
  filename: string
  uploading?: boolean
}

interface ImageUploadManagerProps {
  projectId: number
  value: UploadedImage[]
  onChange: (images: UploadedImage[]) => void
}

export function ImageUploadManager({ projectId, value, onChange }: ImageUploadManagerProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files).filter((file) =>
        file.type.startsWith("image/")
      )

      if (files.length === 0) {
        toast.error("Please drop image files only")
        return
      }

      await uploadFiles(files)
    },
    [projectId, value, onChange]
  )

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (files.length > 0) {
        await uploadFiles(files)
      }
      // Reset input
      e.target.value = ""
    },
    [projectId, value, onChange]
  )

  const uploadFiles = async (files: File[]) => {
    // Add placeholder images while uploading
    const newImages: UploadedImage[] = files.map((file) => ({
      id: `temp-${Math.random()}`,
      url: URL.createObjectURL(file),
      filename: file.name,
      uploading: true
    }))

    onChange([...value, ...newImages])

    // Upload each file
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const tempId = newImages[i].id

      try {
        // Upload to backend
        const result = await uploadImage(projectId, file)

        if (!result.success || !result.data) {
          throw new Error(result.error || "Upload failed")
        }

        // Use the public URL from GCS
        const uploadedImage: UploadedImage = {
          id: result.data.id.toString(),
          url: result.data.gcs_public_url || result.data.gcs_path, // Use public URL
          filename: result.data.filename
        }

        // Replace temp image with uploaded one
        onChange(value.map((img) => (img.id === tempId ? uploadedImage : img)))

        toast.success(`Uploaded ${file.name}`)
      } catch (error) {
        console.error("Upload error:", error)
        toast.error(`Failed to upload ${file.name}`)
        // Remove failed upload
        onChange(value.filter((img) => img.id !== tempId))
      }
    }
  }

  const removeImage = (id: string) => {
    onChange(value.filter((img) => img.id !== id))
    toast.success("Image removed")
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Images</CardTitle>
        <CardDescription>
          Upload images for your email campaign (max 10MB each)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            isDragging
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
          }`}
        >
          <input
            type="file"
            id="image-upload"
            multiple
            accept="image/*"
            onChange={handleFileInput}
            className="sr-only"
          />
          <label
            htmlFor="image-upload"
            className="flex cursor-pointer flex-col items-center gap-2"
          >
            <Upload
              className={`h-10 w-10 ${
                isDragging ? "text-primary" : "text-muted-foreground"
              }`}
            />
            <div>
              <p className="font-medium">
                {isDragging ? "Drop images here" : "Click to upload or drag and drop"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                PNG, JPG, GIF up to 10MB
              </p>
            </div>
          </label>
        </div>

        {/* Uploaded Images Grid */}
        {value.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Uploaded Images ({value.length})</p>
              {value.some((img) => img.uploading) && (
                <Badge variant="secondary">
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  Uploading...
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {value.map((image) => (
                <div
                  key={image.id}
                  className="group relative aspect-square overflow-hidden rounded-lg border bg-muted"
                >
                  {image.uploading ? (
                    <div className="flex h-full items-center justify-center">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <>
                      <img
                        src={image.url}
                        alt={image.filename}
                        className="h-full w-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 transition-opacity group-hover:opacity-100 flex items-center justify-center">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => removeImage(image.id)}
                        >
                          <X className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                        <p className="text-xs text-white truncate">
                          {image.filename}
                        </p>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {value.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <ImageIcon className="h-12 w-12 mb-2 opacity-50" />
            <p className="text-sm">No images uploaded yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

