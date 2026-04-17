"use client"

import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { Calendar, MessageSquare, AlertTriangle, Clock, CheckCircle } from "lucide-react"

export interface Email {
  id: string
  gmail_message_id: string
  gmail_thread_id: string
  sender: string
  senderEmail: string
  subject: string
  summary: string
  category: string
  priority: string
  timestamp: string
  action: string
}

const getActionStyling = (action: string) => {
  const normAction = (action || "").toLowerCase()
  if (normAction.includes("calendar")) {
    return { icon: Calendar, colorClass: "text-blue-400 border-blue-400/30 bg-blue-400/10" }
  }
  if (normAction.includes("reply")) {
    return { icon: MessageSquare, colorClass: "text-yellow-500 border-yellow-500/30 bg-yellow-500/10" }
  }
  if (normAction.includes("required") || normAction.includes("urgent")) {
    return { icon: AlertTriangle, colorClass: "text-orange-500 border-orange-500/30 bg-orange-500/10" }
  }
  if (normAction.includes("decision")) {
    return { icon: Clock, colorClass: "text-purple-400 border-purple-400/30 bg-purple-400/10" }
  }
  return { icon: CheckCircle, colorClass: "text-muted-foreground border-border bg-muted/20" }
}



interface EmailTableProps {
  emails: Email[]
  categoryFilter?: string
  priorityFilter?: string
  searchQuery?: string
  selectedEmailId?: string
  onEmailSelect?: (email: Email) => void
}

export function EmailTable({ 
  emails, 
  categoryFilter, 
  priorityFilter, 
  searchQuery,
  selectedEmailId,
  onEmailSelect
}: EmailTableProps) {
  const filteredEmails = emails.filter((email) => {
    if (categoryFilter && categoryFilter !== "all" && email.category?.toLowerCase() !== categoryFilter.toLowerCase()) {
      return false
    }
    if (priorityFilter && priorityFilter !== "all" && email.priority?.toLowerCase() !== priorityFilter.toLowerCase()) {
      return false
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        email.sender.toLowerCase().includes(query) ||
        email.subject.toLowerCase().includes(query) ||
        email.senderEmail.toLowerCase().includes(query)
      )
    }
    return true
  })

  return (
    <Table>
      <TableHeader className="sticky top-0 z-10 bg-card">
        <TableRow className="border-border hover:bg-transparent">
          <TableHead className="w-[250px] text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sender</TableHead>
          <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Subject & Summary</TableHead>
          <TableHead className="w-[150px] text-xs font-semibold uppercase tracking-wider text-muted-foreground text-right">Received</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredEmails.map((email) => (
          <TableRow
            key={email.id}
            onClick={() => onEmailSelect?.(email)}
            className={cn(
              "cursor-pointer border-border transition-colors hover:bg-muted/50",
              selectedEmailId === email.id ? "bg-muted/40 shadow-[inset_2px_0_0_0_#3b82f6]" : ""
            )}
          >
            <TableCell className="py-4 align-top">
              <div className="flex flex-col gap-1">
                <span className="font-medium text-foreground">{email.sender}</span>
                <span className="text-sm text-muted-foreground">{email.senderEmail}</span>
              </div>
            </TableCell>
            <TableCell className="py-4 align-top">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">{email.subject}</span>
                  {email.priority?.toLowerCase() === "high" && (
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                  )}
                </div>
                <span className="line-clamp-2 text-sm text-muted-foreground">{email.summary}</span>
                <div className="mt-1 flex items-center gap-2">
                  {(() => {
                    const actionLabel = email.action || email.category
                    const { icon: ActionIcon, colorClass } = getActionStyling(actionLabel)
                    return (
                      <Badge variant="outline" className={cn("text-xs capitalize flex items-center gap-1.5 px-2 py-0.5", colorClass)}>
                        <ActionIcon className="h-3 w-3" />
                        {actionLabel}
                      </Badge>
                    )
                  })()}
                </div>
              </div>
            </TableCell>
            <TableCell className="py-4 align-top text-right whitespace-nowrap text-sm text-muted-foreground">
              {email.timestamp}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

