"use server"

import { auth } from "@clerk/nextjs/server"

/**
 * Get authentication token from Clerk for server-side actions
 */
export async function getAuthToken(): Promise<string | null> {
  const { getToken } = auth()
  return getToken()
}
