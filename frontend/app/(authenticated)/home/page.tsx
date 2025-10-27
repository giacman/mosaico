"use client"

import Link from "next/link"
import { FileText, Newspaper, Home as HomeIcon, Bell, Share2, Megaphone } from "lucide-react"
import { Card } from "@/components/ui/card"

const tiles = [
  { title: "LVR Magazine", href: "/magazine", description: "Editorials, long-form content, and complex layouts", icon: FileText, comingSoon: true },
  { title: "Newsletter", href: "/newsletter", description: "Email projects (copy, images, translations)", icon: Newspaper, comingSoon: false },
  { title: "Home Page", href: "/homepage", description: "Hero banners, labels, and HP testing", icon: HomeIcon, comingSoon: true },
  { title: "Push Notification", href: "/push", description: "App push copy and targeting", icon: Bell, comingSoon: true },
  { title: "Social Media", href: "/social", description: "Multi-channel copy and formats", icon: Share2, comingSoon: true },
  { title: "Marketing Campaigns", href: "/marketing", description: "Banners, landing pages, affiliation, programmatic", icon: Megaphone, comingSoon: true }
]

export default function AuthenticatedTilesHome() {
  return (
    <main className="mx-auto w-full max-w-6xl p-6">
      <h1 className="text-2xl font-semibold tracking-tight">Mosaico</h1>
      <p className="text-sm text-muted-foreground mt-1">Select an area to get started.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map(({ title, href, description, icon: Icon, comingSoon }) => (
          <Link key={title} href={href} className="group">
            <Card className="flex h-full flex-col p-6 transition-colors hover:bg-accent/40">
              <div className="flex items-start gap-4">
                <div className="rounded-md bg-primary/10 p-2 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-medium leading-none">{title}</h2>
                    {comingSoon && (
                      <span className="text-[10px] rounded bg-orange-100 px-1.5 py-0.5 text-orange-700">Coming soon</span>
                    )}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{description}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  )
}


