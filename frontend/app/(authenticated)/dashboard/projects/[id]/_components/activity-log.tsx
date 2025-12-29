"use client"

import { useEffect, useState } from "react"
import { getActivityLog, ActivityLog } from "@/actions/projects"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
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
  Clock
} from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { it } from "date-fns/locale"

interface ActivityLogPanelProps {
  projectId: number
}

// Map action types to icons and colors
const actionConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  created_project: { icon: Plus, color: "text-green-500", label: "Created project" },
  updated_project: { icon: Edit, color: "text-blue-500", label: "Updated project" },
  generated_content: { icon: Sparkles, color: "text-purple-500", label: "Generated content" },
  translated_content: { icon: Globe, color: "text-cyan-500", label: "Translated content" },
  uploaded_image: { icon: Upload, color: "text-orange-500", label: "Uploaded image" },
  approved_project: { icon: CheckCircle, color: "text-green-600", label: "Approved project" },
  regenerated_content: { icon: RefreshCw, color: "text-purple-400", label: "Regenerated content" },
  updated_status: { icon: CheckCircle, color: "text-emerald-500", label: "Updated status" },
  updated_brief: { icon: FileText, color: "text-blue-400", label: "Updated brief" },
  updated_structure: { icon: Edit, color: "text-indigo-500", label: "Updated structure" },
}

function getActionConfig(action: string) {
  return actionConfig[action] || { 
    icon: Clock, 
    color: "text-gray-500", 
    label: action.replace(/_/g, " ").replace(/^\w/, c => c.toUpperCase()) 
  }
}

function ActivityLogItem({ log }: { log: ActivityLog }) {
  const config = getActionConfig(log.action)
  const Icon = config.icon
  
  const timeAgo = formatDistanceToNow(new Date(log.created_at), { 
    addSuffix: true,
    locale: it 
  })

  return (
    <div className="flex items-start gap-3 py-3 border-b border-border/50 last:border-0">
      <div className={`mt-0.5 ${config.color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm">
            {log.user_name || "Unknown user"}
          </span>
          <Badge variant="secondary" className="text-xs px-1.5 py-0">
            {config.label}
          </Badge>
        </div>
        {log.field_changed && (
          <p className="text-xs text-muted-foreground mt-0.5">
            Field: <code className="bg-muted px-1 rounded">{log.field_changed}</code>
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-1">
          {timeAgo}
        </p>
      </div>
    </div>
  )
}

function ActivityLogSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start gap-3 py-3">
          <Skeleton className="h-4 w-4 rounded" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function ActivityLogPanel({ projectId }: ActivityLogPanelProps) {
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchLogs() {
      setIsLoading(true)
      const result = await getActivityLog(projectId)
      
      if (result.success && result.data) {
        setLogs(result.data)
        setError(null)
      } else {
        setError(result.error || "Failed to load activity log")
      }
      setIsLoading(false)
    }

    fetchLogs()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchLogs, 30000)
    return () => clearInterval(interval)
  }, [projectId])

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Activity Log
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[400px] pr-4">
          {isLoading ? (
            <ActivityLogSkeleton />
          ) : error ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              {error}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              No activity yet
            </div>
          ) : (
            <div className="space-y-0">
              {logs.map((log) => (
                <ActivityLogItem key={log.id} log={log} />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

