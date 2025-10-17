"use server"

import { auth } from "@clerk/nextjs/server"
import { revalidatePath } from "next/cache"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

export interface SavedComponent {
  component_type: string
  component_index?: number
  generated_content: string
  component_url?: string
  image_id?: number
  translations: Record<string, string> // language_code -> translated_content
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Save generated components to the database
 */
export async function saveGeneratedComponents(
  projectId: number,
  components: SavedComponent[]
): Promise<{ success: boolean; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/projects/${projectId}/components`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        components
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        error: errorData.detail || `Failed to save components: ${response.statusText}`
      }
    }

    // Revalidate the project page to show saved components
    revalidatePath(`/dashboard/projects/${projectId}`)

    return { success: true }
  } catch (error) {
    console.error("Error saving components:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to save components"
    }
  }
}

