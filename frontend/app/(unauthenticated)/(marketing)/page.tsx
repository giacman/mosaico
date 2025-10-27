"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function MarketingPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Mosaico</h1>
        <p className="text-muted-foreground mt-2">Request access or log in if you already have an account</p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button asChild>
            <Link href="#access">Request access</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/login">Log in</Link>
          </Button>
        </div>
        <form id="access" action={async (formData) => {
          const { requestAccess } = await import("@/actions/access")
          const res = await requestAccess(null, formData)
          if (!res.ok) alert(res.error)
          else alert("Request sent. We'll be in touch.")
        }} className="mx-auto mt-8 max-w-sm space-y-3 text-left">
          <input name="name" placeholder="Full name" className="w-full rounded-md border px-3 py-2 text-sm" required />
          <input name="email" type="email" placeholder="Email" className="w-full rounded-md border px-3 py-2 text-sm" required />
          <textarea name="note" placeholder="Notes (optional)" className="w-full rounded-md border px-3 py-2 text-sm" rows={3} />
          <Button type="submit" className="w-full">Send request</Button>
        </form>
      </div>
    </main>
  )
}
