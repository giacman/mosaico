"use client"

import React from "react"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { AlertTriangle, ImageIcon } from "lucide-react"

interface ImageUploadGuardProps {
    isOpen: boolean
    onClose: () => void
    onConfirm: () => void
    missingCount: number
}

export function ImageUploadGuard({
    isOpen,
    onClose,
    onConfirm,
    missingCount
}: ImageUploadGuardProps) {
    return (
        <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <AlertDialogContent className="max-w-[400px]">
                <AlertDialogHeader>
                    <div className="flex items-center gap-2 mb-2 text-warning">
                        <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
                            <AlertTriangle className="h-6 w-6 text-amber-600" />
                        </div>
                        <AlertDialogTitle className="text-xl">Missing Images</AlertDialogTitle>
                    </div>
                    <AlertDialogDescription className="text-sm">
                        You have <span className="font-bold text-foreground">{missingCount} image placeholder(s)</span> without an uploaded image.
                        <br /><br />
                        Generating content without images might result in less relevant context. Do you want to continue anyway?
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className="flex-col sm:flex-row gap-2">
                    <AlertDialogCancel onClick={onClose} className="flex-1">
                        Go Back & Upload
                    </AlertDialogCancel>
                    <AlertDialogAction
                        onClick={onConfirm}
                        className="flex-1 bg-amber-600 hover:bg-amber-700 text-white border-none"
                    >
                        Continue Generation
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}
