"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Sparkles, AlertCircle, TrendingUp, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

export interface InsightData {
  type: "urgent" | "info" | "trend"
  title: string
  description: string
}

interface AIInsightsProps {
  insightsData: InsightData[]
  totalEmails: number
  urgentCount: number
  onViewUrgent?: () => void
}

const typeColors = {
  urgent: "text-status-danger bg-status-danger/10",
  info: "text-status-info bg-status-info/10",
  trend: "text-status-success bg-status-success/10",
}

const getIcon = (type: string) => {
  if (type === "urgent") return <AlertCircle className="h-4 w-4" />
  if (type === "info") return <Clock className="h-4 w-4" />
  return <TrendingUp className="h-4 w-4" />
}

export function AIInsights({ insightsData, totalEmails, urgentCount, onViewUrgent }: AIInsightsProps) {
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
            Today you received <span className="font-semibold text-primary">{totalEmails} emails</span>, with{" "}
            {urgentCount > 0 ? (
              <span className="font-semibold text-status-danger">{urgentCount} marked as urgent</span>
            ) : (
              <span className="font-semibold text-status-success">0 marked as urgent</span>
            )}
            . Your inbox health is looking good.
          </p>
        </div>

        {/* Insight items */}
        <div className="flex flex-col gap-2">
          {insightsData.map((insight, index) => (
            <div
              key={index}
              className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-3 transition-colors hover:bg-muted/50"
            >
              <div className={cn("rounded-md p-1.5", typeColors[insight.type])}>
                {getIcon(insight.type)}
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
            <button 
              onClick={onViewUrgent}
              className="rounded-md bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
            >
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
