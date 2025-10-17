"use server"

import { auth } from "@clerk/nextjs/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

interface ImageUploadResult {
  id: number
  project_id: number
  filename: string
  gcs_path: string
  gcs_public_url: string | null
  uploaded_at: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Upload an image file to GCS via backend
 */
export async function uploadImage(
  projectId: number,
  file: File
): Promise<{ success: boolean; data?: ImageUploadResult; error?: string }> {
  try {
    const token = await getAuthToken()

    const formData = new FormData()
    formData.append("file", file)
    formData.append("project_id", projectId.toString())

    const response = await fetch(`${API_URL}/api/v1/upload-image`, {
      method: "POST",
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: formData
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Upload image error:", errorText)
      return {
        success: false,
        error: `Failed to upload image: ${response.status}`
      }
    }

    const data: ImageUploadResult = await response.json()

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error("Error uploading image:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

