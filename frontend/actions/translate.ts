"use server"

import { auth } from "@clerk/nextjs/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080"

interface TranslateContentInput {
  text: string
  target_language: string
  source_language?: string
  maintain_tone?: boolean
  content_type?: string
}

interface TranslateContentResult {
  translated_text: string
  original_text: string
  target_language: string
  source_language: string
}

/**
 * Get authentication token from Clerk
 */
async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth()
  return getToken()
}

/**
 * Translate text content to target language
 */
export async function translateContent(
  input: TranslateContentInput
): Promise<{ success: boolean; data?: TranslateContentResult; error?: string }> {
  try {
    const token = await getAuthToken()

    const response = await fetch(`${BACKEND_URL}/api/v1/translate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify({
        text: input.text,
        target_language: input.target_language,
        source_language: input.source_language || "en",
        maintain_tone: input.maintain_tone ?? true,
        content_type: input.content_type || "newsletter"
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Translate content error:", errorText)
      return {
        success: false,
        error: `Failed to translate content: ${response.status}`
      }
    }

    const data: TranslateContentResult = await response.json()

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error("Error translating content:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

/**
 * Batch translate multiple texts to multiple languages
 */
export async function batchTranslate(
  texts: { key: string; content: string }[],
  targetLanguages: string[]
): Promise<{
  success: boolean
  data?: Record<string, Record<string, string>> // { componentKey: { lang: translatedText } }
  error?: string
}> {
  try {
    const translations: Record<string, Record<string, string>> = {}

    // Translate each text to each language
    for (const { key, content } of texts) {
      translations[key] = {}

      for (const lang of targetLanguages) {
        const result = await translateContent({
          text: content,
          target_language: lang
        })

        if (result.success && result.data) {
          translations[key][lang] = result.data.translated_text
        } else {
          // If one translation fails, we still continue with others
          translations[key][lang] = `[Translation failed: ${result.error}]`
        }
      }
    }

    return {
      success: true,
      data: translations
    }
  } catch (error) {
    console.error("Error in batch translation:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

