"use server"

import { auth } from "@clerk/nextjs/server"
import { revalidatePath } from "next/cache"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface Label {
  id: number
  name: string
  color: string
  description: string | null
  created_by_user_name: string | null
}

export interface CreateLabelInput {
  name: string
  color?: string
  description?: string
}

export interface UpdateLabelInput {
  name?: string
  color?: string
  description?: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * List all labels
 */
export async function listLabels(): Promise<{
  success: boolean
  data?: Label[]
  error?: string
}> {
  try {
    const token = await getAuthToken()
    
    const response = await fetch(`${API_URL}/api/v1/labels`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      cache: "no-store"
    })

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to fetch labels: ${response.statusText}`
      }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error("Error listing labels:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to list labels"
    }
  }
}

/**
 * Create a new label
 */
export async function createLabel(
  input: CreateLabelInput
): Promise<{ success: boolean; data?: Label; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/labels`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(input)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        error: errorData.detail || `Failed to create label: ${response.statusText}`
      }
    }

    const data = await response.json()
    
    // Revalidate dashboard to refresh labels
    revalidatePath("/dashboard")
    
    return { success: true, data }
  } catch (error) {
    console.error("Error creating label:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to create label"
    }
  }
}

/**
 * Update a label
 */
export async function updateLabel(
  id: number,
  input: UpdateLabelInput
): Promise<{ success: boolean; data?: Label; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/labels/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(input)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        error: errorData.detail || `Failed to update label: ${response.statusText}`
      }
    }

    const data = await response.json()
    
    revalidatePath("/dashboard")
    
    return { success: true, data }
  } catch (error) {
    console.error("Error updating label:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to update label"
    }
  }
}

/**
 * Delete a label
 */
export async function deleteLabel(
  id: number
): Promise<{ success: boolean; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/labels/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to delete label: ${response.statusText}`
      }
    }

    revalidatePath("/dashboard")

    return { success: true }
  } catch (error) {
    console.error("Error deleting label:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to delete label"
    }
  }
}

