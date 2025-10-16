"use server"

import { auth } from "@clerk/nextjs/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080"

interface OptimizePromptInput {
  text: string
  content_type: string
  tone: string
  structure: Array<{ component: string; count: number }>
}

interface OptimizePromptResult {
  optimized_prompt: string
  improvements: string[]
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Optimize a user's brief/prompt for better AI generation
 */
export async function optimizePrompt(
  input: OptimizePromptInput
): Promise<{ success: boolean; data?: OptimizePromptResult; error?: string }> {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${BACKEND_URL}/api/v1/optimize-prompt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify(input)
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Optimize prompt error:", errorText)
      return {
        success: false,
        error: `Failed to optimize prompt: ${response.status}`
      }
    }

    const data: OptimizePromptResult = await response.json()

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error("Error optimizing prompt:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

