"use client"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from "@/components/ui/alert-dialog"
import { AlertCircle } from "lucide-react"

interface MissingImagesDialogProps {
  open: boolean
  sectionsWithoutImages: Array<{ key: string; name: string }>
  onCancel: () => void
  onProceedAnyway: () => void
}

export function MissingImagesDialog({
  open,
  sectionsWithoutImages,
  onCancel,
  onProceedAnyway
}: MissingImagesDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-amber-100 p-2">
              <AlertCircle className="h-5 w-5 text-amber-600" />
            </div>
            <AlertDialogTitle>Missing Images</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="space-y-3 pt-2">
            <p>
              The following sections don't have images:
            </p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              {sectionsWithoutImages.map((section) => (
                <li key={section.key} className="text-sm">
                  <span className="font-medium">{section.name}</span>
                </li>
              ))}
            </ul>
            <p className="text-sm">
              Adding images helps the AI generate more relevant and contextualized 
              content. We recommend uploading at least one image per section.
            </p>
            <p className="text-sm font-medium">
              Do you want to add images or proceed anyway?
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>
            Upload Images
          </AlertDialogCancel>
          <AlertDialogAction onClick={onProceedAnyway}>
            Proceed Anyway
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

