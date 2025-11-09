"use client"

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from "react"
import { Notification, NotificationCenter } from "@/components/ui/notification-center"
import { toast } from "sonner"

interface NotificationsContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  dismissNotification: (id: string) => void
}

const NotificationsContext = createContext<NotificationsContextType | undefined>(undefined)

export function useNotifications() {
  const context = useContext(NotificationsContext)
  if (!context) {
    throw new Error("useNotifications must be used within NotificationsProvider")
  }
  return context
}

interface NotificationsProviderProps {
  children: ReactNode
}

export function NotificationsProvider({ children }: NotificationsProviderProps) {
  const storageKey = "mosaico:notifications"
  const [notifications, setNotifications] = useState<Notification[]>(() => {
    if (typeof window === "undefined") return []
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) return []
      const arr = JSON.parse(raw)
      if (!Array.isArray(arr)) return []
      return arr.map((n: any) => ({
        id: String(n.id || ""),
        type: n.type === "error" ? "error" : n.type === "success" ? "success" : "info",
        title: String(n.title || ""),
        message: String(n.message || ""),
        timestamp: n.timestamp ? new Date(n.timestamp) : new Date(),
        read: Boolean(n.read)
      })) as Notification[]
    } catch {
      return []
    }
  })

  // Load persisted notifications
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw) {
        const arr = JSON.parse(raw)
        if (Array.isArray(arr)) {
          // revive timestamps
          const revived: Notification[] = arr.map((n: any) => ({
            id: String(n.id || ""),
            type: n.type === "error" ? "error" : n.type === "success" ? "success" : "info",
            title: String(n.title || ""),
            message: String(n.message || ""),
            timestamp: n.timestamp ? new Date(n.timestamp) : new Date(),
            read: Boolean(n.read)
          }))
          setNotifications(revived)
        }
      }
    } catch {}
  }, [])

  // Persist on change
  useEffect(() => {
    try {
      const serializable = notifications.map(n => ({ ...n, timestamp: n.timestamp.toISOString() }))
      localStorage.setItem(storageKey, JSON.stringify(serializable))
    } catch {}
  }, [notifications])

  const addNotification = useCallback((notification: Omit<Notification, "id" | "timestamp" | "read">) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      read: false
    }
    
    setNotifications((prev) => [newNotification, ...prev])
    // Write immediately so a quick navigation still shows badge after reload
    try {
      const raw = localStorage.getItem(storageKey)
      const prev = raw ? JSON.parse(raw) : []
      const serializable = [{ ...newNotification, timestamp: newNotification.timestamp.toISOString() }, ...(Array.isArray(prev) ? prev : [])]
      localStorage.setItem(storageKey, JSON.stringify(serializable))
    } catch {}
    
    // Also show a toast for immediate feedback
    toast(notification.title, {
      description: notification.message
    })
  }, [])

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  return (
    <NotificationsContext.Provider
      value={{
        notifications,
        addNotification,
        markAsRead,
        markAllAsRead,
        dismissNotification
      }}
    >
      {children}
    </NotificationsContext.Provider>
  )
}

/**
 * NotificationBell component to be placed in the header
 * Uses the notifications context
 */
export function NotificationBell() {
  const { notifications, markAsRead, markAllAsRead, dismissNotification } = useNotifications()
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])
  
  return (
    <>
      {isClient && (
        <NotificationCenter
          notifications={notifications}
          onMarkAsRead={markAsRead}
          onMarkAllAsRead={markAllAsRead}
          onDismiss={dismissNotification}
        />
      )}
    </>
  )
}

