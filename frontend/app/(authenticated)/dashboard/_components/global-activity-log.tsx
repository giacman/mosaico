"use client"

import { useEffect, useState, useCallback } from "react"
import { getGlobalActivityLog, GlobalActivityLog } from "@/actions/projects"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  FileText, 
  Sparkles, 
  Globe, 
  Upload, 
  Edit, 
  Plus,
  CheckCircle,
  RefreshCw,
  Clock,
  ClipboardList,
  ChevronDown
} from "lucide-react"
import { format, formatDistanceToNow } from "date-fns"
import { it } from "date-fns/locale"
import Link from "next/link"

// Map action types to icons and colors
const actionConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  created_project: { icon: Plus, color: "text-green-500", label: "Created" },
  updated_project: { icon: Edit, color: "text-blue-500", label: "Updated" },
  generated_content: { icon: Sparkles, color: "text-purple-500", label: "Generated" },
  translated_content: { icon: Globe, color: "text-cyan-500", label: "Translated" },
  uploaded_image: { icon: Upload, color: "text-orange-500", label: "Uploaded image" },
  approved_project: { icon: CheckCircle, color: "text-green-600", label: "Approved" },
  regenerated_content: { icon: RefreshCw, color: "text-purple-400", label: "Regenerated" },
  updated_status: { icon: CheckCircle, color: "text-emerald-500", label: "Status change" },
  updated_brief: { icon: FileText, color: "text-blue-400", label: "Brief updated" },
  updated_structure: { icon: Edit, color: "text-indigo-500", label: "Structure updated" },
}

function getActionConfig(action: string) {
  return actionConfig[action] || { 
    icon: Clock, 
    color: "text-gray-500", 
    label: action.replace(/_/g, " ").replace(/^\w/, c => c.toUpperCase()) 
  }
}

function ActivityLogItem({ log, showFullDate }: { log: GlobalActivityLog; showFullDate?: boolean }) {
  const config = getActionConfig(log.action)
  const Icon = config.icon
  
  const date = new Date(log.created_at)
  const timeDisplay = showFullDate 
    ? format(date, "d MMM yyyy, HH:mm", { locale: it })
    : formatDistanceToNow(date, { addSuffix: true, locale: it })

  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border/50 last:border-0 hover:bg-muted/30 px-2 -mx-2 rounded">
      <div className={`mt-0.5 ${config.color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm truncate">
            {log.user_name || "Unknown"}
          </span>
          <Badge variant="secondary" className="text-xs px-1.5 py-0 shrink-0">
            {config.label}
          </Badge>
        </div>
        <Link 
          href={`/dashboard/projects/${log.project_id}`}
          className="text-xs text-primary hover:underline truncate block mt-0.5"
        >
          {log.project_name}
        </Link>
        <p className="text-xs text-muted-foreground mt-0.5" title={format(date, "d MMMM yyyy, HH:mm:ss", { locale: it })}>
          {timeDisplay}
        </p>
      </div>
    </div>
  )
}

function ActivityLogSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start gap-3 py-2">
          <Skeleton className="h-4 w-4 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>
      ))}
    </div>
  )
}

const PAGE_SIZE = 25

export function GlobalActivityLog() {
  const [logs, setLogs] = useState<GlobalActivityLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [showFullDates, setShowFullDates] = useState(false)

  const fetchLogs = useCallback(async (limit: number, append = false) => {
    if (append) {
      setIsLoadingMore(true)
    } else {
      setIsLoading(true)
    }
    
    const result = await getGlobalActivityLog(limit)
    
    if (result.success && result.data) {
      if (append) {
        setLogs(result.data)
      } else {
        setLogs(result.data)
      }
      // If we got fewer items than requested, there's no more
      setHasMore(result.data.length >= limit)
      setError(null)
    } else {
      setError(result.error || "Failed to load activity")
    }
    
    setIsLoading(false)
    setIsLoadingMore(false)
  }, [])

  useEffect(() => {
    fetchLogs(PAGE_SIZE)
  }, [fetchLogs])

  const loadMore = () => {
    const newLimit = logs.length + PAGE_SIZE
    fetchLogs(newLimit, true)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <ClipboardList className="h-4 w-4" />
            Activity Log
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs"
            onClick={() => setShowFullDates(!showFullDates)}
          >
            {showFullDates ? "Relative" : "Full dates"}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Complete audit trail of all team actions
        </p>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[400px] pr-2">
          {isLoading ? (
            <ActivityLogSkeleton />
          ) : error ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              {error}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              No activity recorded yet
            </div>
          ) : (
            <div className="space-y-0">
              {logs.map((log) => (
                <ActivityLogItem 
                  key={log.id} 
                  log={log} 
                  showFullDate={showFullDates}
                />
              ))}
              
              {/* Load More button */}
              {hasMore && (
                <div className="pt-4 pb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={loadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? (
                      <>
                        <RefreshCw className="h-3 w-3 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3 mr-2" />
                        Load more history
                      </>
                    )}
                  </Button>
                </div>
              )}
              
              {!hasMore && logs.length > 0 && (
                <p className="text-xs text-muted-foreground text-center py-4">
                  — End of activity log —
                </p>
              )}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

