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
            <AlertDialogContent className="max-w-[450px]">
                <AlertDialogHeader>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                            <AlertTriangle className="h-5 w-5 text-amber-600" />
                        </div>
                        <div>
                            <AlertDialogTitle>Missing Component Images</AlertDialogTitle>
                            <AlertDialogDescription className="mt-1">
                                Action Required
                            </AlertDialogDescription>
                        </div>
                    </div>
                    <div className="py-2 text-sm text-muted-foreground">
                        <p>
                            You have <span className="font-semibold text-amber-600">{missingCount} component(s)</span> (e.g. Image or Header) that require an image but none was uploaded.
                        </p>
                        <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
                            <li>The AI context will be missing visual cues.</li>
                            <li>The generated text might not match your visual content.</li>
                        </ul>
                    </div>
                </AlertDialogHeader>
                <AlertDialogFooter className="flex-col sm:flex-row gap-2 mt-2">
                    <AlertDialogCancel onClick={onClose} className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground border-primary">
                        <ImageIcon className="mr-2 h-4 w-4" />
                        Go Upload Images
                    </AlertDialogCancel>
                    <AlertDialogAction
                        onClick={onConfirm}
                        className="flex-1 bg-transparent text-muted-foreground hover:bg-destructive/10 hover:text-destructive border border-input shadow-none"
                    >
                        Proceed without Images
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}
