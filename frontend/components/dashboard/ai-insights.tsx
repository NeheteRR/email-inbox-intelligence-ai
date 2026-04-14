"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Sparkles, AlertCircle, TrendingUp, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

interface InsightItem {
  icon: React.ReactNode
  title: string
  description: string
  type: "urgent" | "info" | "trend"
}

const insights: InsightItem[] = [
  {
    icon: <AlertCircle className="h-4 w-4" />,
    title: "3 urgent emails",
    description: "Require your attention today",
    type: "urgent",
  },
  {
    icon: <Clock className="h-4 w-4" />,
    title: "2 meeting invites",
    description: "Pending your response",
    type: "info",
  },
  {
    icon: <TrendingUp className="h-4 w-4" />,
    title: "Email volume up 12%",
    description: "Compared to last week",
    type: "trend",
  },
]

const typeColors = {
  urgent: "text-status-danger bg-status-danger/10",
  info: "text-status-info bg-status-info/10",
  trend: "text-status-success bg-status-success/10",
}

export function AIInsights() {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <div className="rounded-md bg-primary/10 p-1.5">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          AI Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {/* Summary */}
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-foreground">
            Today you received <span className="font-semibold text-primary">24 emails</span>, with{" "}
            <span className="font-semibold text-status-danger">3 marked as urgent</span>. Your inbox health is looking good.
          </p>
        </div>

        {/* Insight items */}
        <div className="flex flex-col gap-2">
          {insights.map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-3 transition-colors hover:bg-muted/50"
            >
              <div className={cn("rounded-md p-1.5", typeColors[insight.type])}>
                {insight.icon}
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-sm font-medium text-foreground">{insight.title}</span>
                <span className="text-xs text-muted-foreground">{insight.description}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-2 border-t border-border pt-3">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Quick Actions
          </p>
          <div className="flex flex-wrap gap-2">
            <button className="rounded-md bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20">
              View Urgent
            </button>
            <button className="rounded-md bg-muted px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted/80">
              Schedule Time
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
