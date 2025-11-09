"use server"

import { auth } from "@clerk/nextjs/server"
import { getAuthToken } from "@/actions/generate"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

export type OptimizePromptParams = {
  prompt: string
  content_type: string
  tone: string
  structure: Array<{ component: string; count: number }>
}

interface OptimizePromptResult {
  optimized_prompt: string
  improvements: string[]
}

/**
 * Optimize a user's brief/prompt for better AI generation
 */
export async function optimizePrompt(params: OptimizePromptParams) {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${API_URL}/api/v1/optimize-prompt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify(params)
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

