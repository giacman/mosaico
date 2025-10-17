"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from "react"
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
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback((notification: Omit<Notification, "id" | "timestamp" | "read">) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      read: false
    }
    
    setNotifications((prev) => [newNotification, ...prev])
    
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
  
  return (
    <NotificationCenter
      notifications={notifications}
      onMarkAsRead={markAsRead}
      onMarkAllAsRead={markAllAsRead}
      onDismiss={dismissNotification}
    />
  )
}

