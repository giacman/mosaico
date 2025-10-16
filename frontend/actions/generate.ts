"use server"

import { auth } from "@clerk/nextjs/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080"

interface GenerateContentInput {
  text: string
  count: number
  tone: string
  content_type: string
  structure: Array<{ component: string; count: number }>
  context?: string
  image_url?: string
}

interface GeneratedContent {
  [key: string]: string // e.g., { "subject": "...", "pre_header": "...", "body_1": "...", "cta_1": "..." }
}

interface GenerateContentResult {
  variations: GeneratedContent[]
  original_text: string
  tone: string
  content_type: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Generate email content variations using AI
 */
export async function generateContent(
  input: GenerateContentInput
): Promise<{ success: boolean; data?: GenerateContentResult; error?: string }> {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${BACKEND_URL}/api/v1/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify(input)
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Generate content error:", errorText)
      return {
        success: false,
        error: `Failed to generate content: ${response.status}`
      }
    }

    const data: GenerateContentResult = await response.json()

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error("Error generating content:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

