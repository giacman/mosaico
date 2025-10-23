"use client"

import { SignUp } from "@clerk/nextjs"
import { dark } from "@clerk/themes"
import { useTheme } from "next-themes"

export default function SignUpPage() {
  const { theme } = useTheme()
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <SignUp forceRedirectUrl="/home" signInUrl="/login" appearance={{ baseTheme: theme === "dark" ? dark : undefined }} />
    </div>
  )
}
