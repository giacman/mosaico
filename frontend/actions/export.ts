"use server"

import { getAuthToken } from "@/actions/generate"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

export type HandlebarsGenerateParams = {
  project_id: number
  component_key: string
  translations: Record<string, string> // {lang_code: translated_text}
  english_fallback: string
}

interface HandlebarGenerateResult {
  component_key: string
  handlebar_template: string
}

/**
 * Generate handlebar template for a component with translations
 */
export async function handlebarsGenerate(
  params: HandlebarsGenerateParams
): Promise<any> {
  const token = await getAuthToken()

  const response = await fetch(`${API_URL}/api/v1/handlebars/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` })
    },
    body: JSON.stringify(params)
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
}

