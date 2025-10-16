"use server"

import { auth } from "@clerk/nextjs/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

export interface Project {
  id: number
  name: string
  brief_text: string | null
  structure: Array<{ component: string; count: number }>
  tone: string | null
  target_languages: string[]
  created_by_user_id: string | null
  created_by_user_name: string | null
  updated_by_user_id: string | null
  updated_by_user_name: string | null
  created_at: string
  updated_at: string
}

export interface CreateProjectInput {
  name: string
  brief_text?: string
  structure: Array<{ component: string; count: number }>
  tone?: string
  target_languages?: string[]
}

export interface UpdateProjectInput {
  name?: string
  brief_text?: string
  structure?: Array<{ component: string; count: number }>
  tone?: string
  target_languages?: string[]
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * List all projects
 */
export async function listProjects(): Promise<{
  success: boolean
  data?: Project[]
  error?: string
}> {
  try {
    const token = await getAuthToken()
    
    const response = await fetch(`${API_URL}/api/v1/projects`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      cache: "no-store"
    })

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to fetch projects: ${response.statusText}`
      }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error("Error listing projects:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to list projects"
    }
  }
}

/**
 * Get a single project by ID
 */
export async function getProject(
  id: number
): Promise<{ success: boolean; data?: Project; error?: string }> {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${API_URL}/api/v1/projects/${id}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      cache: "no-store"
    })

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to fetch project: ${response.statusText}`
      }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error("Error getting project:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to get project"
    }
  }
}

/**
 * Create a new project
 */
export async function createProject(
  input: CreateProjectInput
): Promise<{ success: boolean; data?: Project; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/projects`, {
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
        error: errorData.detail || `Failed to create project: ${response.statusText}`
      }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error("Error creating project:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to create project"
    }
  }
}

/**
 * Update a project
 */
export async function updateProject(
  id: number,
  input: UpdateProjectInput
): Promise<{ success: boolean; data?: Project; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/projects/${id}`, {
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
        error: errorData.detail || `Failed to update project: ${response.statusText}`
      }
    }

    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    console.error("Error updating project:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to update project"
    }
  }
}

/**
 * Delete a project
 */
export async function deleteProject(
  id: number
): Promise<{ success: boolean; error?: string }> {
  try {
    const token = await getAuthToken()

    if (!token) {
      return { success: false, error: "Not authenticated" }
    }

    const response = await fetch(`${API_URL}/api/v1/projects/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    if (!response.ok) {
      return {
        success: false,
        error: `Failed to delete project: ${response.statusText}`
      }
    }

    return { success: true }
  } catch (error) {
    console.error("Error deleting project:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to delete project"
    }
  }
}

