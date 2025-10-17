"use server"

import { auth } from "@clerk/nextjs/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080"

interface HandlebarGenerateInput {
  component_key: string
  translations: Record<string, string> // {lang_code: translated_text}
  english_fallback: string
}

interface HandlebarGenerateResult {
  component_key: string
  handlebar_template: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Generate handlebar template for a component with translations
 */
export async function generateHandlebar(
  input: HandlebarGenerateInput
): Promise<{ success: boolean; data?: HandlebarGenerateResult; error?: string }> {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${BACKEND_URL}/api/v1/handlebars/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify(input)
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Generate handlebar error:", errorText)
      return {
        success: false,
        error: `Failed to generate handlebar: ${response.status}`
      }
    }

    const data: HandlebarGenerateResult = await response.json()

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error("Error generating handlebar:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

