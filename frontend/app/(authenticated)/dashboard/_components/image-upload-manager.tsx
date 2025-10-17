"use client"

import { useState } from "react"
import { Upload, X, Image as ImageIcon, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { uploadImage } from "@/actions/upload"
import imageCompression from "browser-image-compression"

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

  const compressImage = async (file: File): Promise<File> => {
    // Skip compression for very small files (< 100KB)
    if (file.size < 100 * 1024) {
      return file
    }

    const originalSizeMB = (file.size / 1024 / 1024).toFixed(2)
    
    try {
      const options = {
        maxSizeMB: 2, // Max file size 2MB
        maxWidthOrHeight: 1920, // Max dimension for email images
        useWebWorker: true, // Use web worker for better performance
        fileType: 'image/jpeg', // Convert to JPEG for better compression
        initialQuality: 0.8 // Good balance between quality and size
      }

      const compressedFile = await imageCompression(file, options)
      const compressedSizeMB = (compressedFile.size / 1024 / 1024).toFixed(2)
      
      console.log(`Image compressed: ${originalSizeMB}MB → ${compressedSizeMB}MB`)
      
      // Show toast if significant compression occurred
      if (file.size / compressedFile.size > 1.5) {
        toast.success(`Image compressed: ${originalSizeMB}MB → ${compressedSizeMB}MB`)
      }
      
      return compressedFile
    } catch (error) {
      console.error('Compression error:', error)
      toast.warning(`Using original image (${originalSizeMB}MB)`)
      return file
    }
  }

  const uploadFiles = async (files: File[]) => {
    // Validate file sizes first
    const MAX_ORIGINAL_SIZE = 10 * 1024 * 1024 // 10MB original size limit
    const invalidFiles = files.filter(f => f.size > MAX_ORIGINAL_SIZE)
    
    if (invalidFiles.length > 0) {
      toast.error(`Files too large (max 10MB): ${invalidFiles.map(f => f.name).join(', ')}`)
      return
    }

    // Add placeholder images while uploading
    const newImages: UploadedImage[] = files.map((file) => ({
      id: `temp-${Math.random()}`,
      url: URL.createObjectURL(file),
      filename: file.name,
      uploading: true
    }))

    // Keep track of current images state
    let currentImages = [...value, ...newImages]
    onChange(currentImages)

    // Upload each file
    for (let i = 0; i < files.length; i++) {
      const originalFile = files[i]
      const tempId = newImages[i].id

      try {
        // Compress image before upload
        toast.info(`Compressing ${originalFile.name}...`)
        const compressedFile = await compressImage(originalFile)
        
        // Upload to backend
        const result = await uploadImage(projectId, compressedFile)

        if (!result.success || !result.data) {
          throw new Error(result.error || "Upload failed")
        }

        // Use the public URL from GCS
        const uploadedImage: UploadedImage = {
          id: result.data.id.toString(),
          url: result.data.gcs_public_url || result.data.gcs_path, // Use public URL
          filename: result.data.filename
        }

        // Replace temp image with uploaded one using current state
        currentImages = currentImages.map((img) => (img.id === tempId ? uploadedImage : img))
        onChange(currentImages)

        toast.success(`Uploaded ${originalFile.name}`)
      } catch (error) {
        console.error("Upload error:", error)
        toast.error(`Failed to upload ${originalFile.name}`)
        // Remove failed upload using current state
        currentImages = currentImages.filter((img) => img.id !== tempId)
        onChange(currentImages)
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files).filter((file) =>
      file.type.startsWith("image/")
    )
    if (files.length > 0) {
      uploadFiles(files)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      uploadFiles(Array.from(files))
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
          Upload images for your email campaign (max 10MB, auto-compressed to 2MB)
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

