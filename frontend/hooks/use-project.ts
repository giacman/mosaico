"use client"

import useSWR from "swr"
import { getProject } from "@/actions/projects"

/**
 * Hook to fetch and manage project data with automatic revalidation
 * Replaces server props pattern with client-side SWR for better state sync
 */
export function useProject(projectId: number) {
  const { data, error, isLoading, mutate } = useSWR(
    projectId ? `/api/projects/${projectId}` : null,
    async () => {
      const result = await getProject(projectId)
      if (!result.success || !result.data) {
        throw new Error(result.error || "Failed to fetch project")
      }
      return result.data
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 2000,
    }
  )

  /**
   * Refresh project data from server
   * Call this after any mutation (upload, save, generate, etc.)
   */
  const refresh = async () => {
    await mutate()
  }

  return {
    project: data,
    isLoading,
    error,
    refresh,
    mutate
  }
}
