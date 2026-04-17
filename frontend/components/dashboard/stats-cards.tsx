"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Mail, AlertTriangle, Calendar, MailOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  change?: string
  changeType?: "increase" | "decrease" | "neutral"
  icon: React.ReactNode
  iconColor?: string
}

function StatCard({ title, value, change, changeType = "neutral", icon, iconColor }: StatCardProps) {
  return (
    <Card className="border-border bg-card transition-all duration-200 hover:border-primary/30">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {title}
            </span>
            <span className="text-2xl font-bold text-card-foreground">{value}</span>
            {change && (
              <span
                className={cn(
                  "text-xs font-medium",
                  changeType === "increase" && "text-status-success",
                  changeType === "decrease" && "text-status-danger",
                  changeType === "neutral" && "text-muted-foreground"
                )}
              >
                {change}
              </span>
            )}
          </div>
          <div className={cn("rounded-lg p-2.5", iconColor || "bg-primary/10")}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export interface DashboardStats {
  total_emails: number
  high_priority: number
  meetings_detected: number
  unread_emails: number
}

interface StatsCardsProps {
  statsData: DashboardStats | null
}

export function StatsCards({ statsData }: StatsCardsProps) {
  const stats = [
    {
      title: "Total Emails",
      value: statsData?.total_emails || 0,
      change: "Processed today",
      changeType: "neutral" as const,
      icon: <Mail className="h-5 w-5 text-primary" />,
      iconColor: "bg-primary/10",
    },
    {
      title: "High Priority",
      value: statsData?.high_priority || 0,
      change: "Require action",
      changeType: "neutral" as const,
      icon: <AlertTriangle className="h-5 w-5 text-status-danger" />,
      iconColor: "bg-status-danger/10",
    },
    {
      title: "Meetings Detected",
      value: statsData?.meetings_detected || 0,
      change: "Upcoming today",
      changeType: "neutral" as const,
      icon: <Calendar className="h-5 w-5 text-status-info" />,
      iconColor: "bg-status-info/10",
    },
    {
      title: "Unread Emails",
      value: statsData?.unread_emails || 0,
      change: "Needs reply",
      changeType: "neutral" as const,
      icon: <MailOpen className="h-5 w-5 text-status-success" />,
      iconColor: "bg-status-success/10",
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <StatCard key={stat.title} {...stat} />
      ))}
    </div>
  )
}
