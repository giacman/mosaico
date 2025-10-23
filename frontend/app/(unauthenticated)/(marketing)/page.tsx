"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function MarketingPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Mosaico</h1>
        <p className="text-muted-foreground mt-2">Accedi o registrati per continuare</p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button asChild>
            <Link href="/signup">Sign up</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/login">Log in</Link>
          </Button>
        </div>
      </div>
    </main>
  )
}
