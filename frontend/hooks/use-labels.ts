"use client"

import useSWR from "swr"
import { listLabels, Label } from "@/actions/labels"

/**
 * SWR hook for fetching all available labels
 * Provides caching and automatic revalidation
 */
export function useLabels() {
  const { data, error, isLoading, mutate } = useSWR<Label[]>(
    "labels",
    async () => {
      const result = await listLabels()
      if (result.success && result.data) {
        return result.data
      }
      throw new Error(result.error || "Failed to fetch labels")
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60000 // Cache for 1 minute
    }
  )

  return {
    labels: data || [],
    isLoading,
    error,
    refresh: mutate
  }
}

