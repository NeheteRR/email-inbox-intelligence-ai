"use client"

import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Mail,
  AlertCircle,
  Calendar,
  Settings,
  Sparkles,
} from "lucide-react"

interface SidebarProps {
  activeItem?: string
  onItemClick?: (item: string) => void
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "all-emails", label: "All Emails", icon: Mail },
  { id: "priority", label: "Priority Emails", icon: AlertCircle },
  { id: "meetings", label: "Meetings", icon: Calendar },
  { id: "settings", label: "Settings", icon: Settings },
]

export function Sidebar({ activeItem = "dashboard", onItemClick }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-sidebar-border bg-sidebar">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-sidebar-border px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
          <Sparkles className="h-5 w-5 text-primary-foreground" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-sidebar-foreground">CloudMail AI</span>
          <span className="text-xs text-muted-foreground">Email Intelligence</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeItem === item.id
            return (
              <li key={item.id}>
                <button
                  onClick={() => onItemClick?.(item.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-primary"
                      : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive && "text-sidebar-primary")} />
                  {item.label}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-border px-4 py-4">
        <div className="rounded-lg bg-sidebar-accent/50 p-3">
          <p className="text-xs font-medium text-muted-foreground">AI Analysis</p>
          <p className="mt-1 text-xs text-sidebar-foreground">
            12 emails analyzed today
          </p>
        </div>
      </div>
    </aside>
  )
}
