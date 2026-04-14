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

interface Email {
  id: string
  sender: string
  senderEmail: string
  subject: string
  summary: string
  category: "work" | "meeting" | "personal" | "newsletter" | "spam"
  priority: "high" | "medium" | "low"
  timestamp: string
}

const sampleEmails: Email[] = [
  {
    id: "1",
    sender: "Sarah Johnson",
    senderEmail: "sarah.j@company.com",
    subject: "Q4 Budget Review Meeting",
    summary: "Requesting your presence for the quarterly budget review. Key topics include department allocations and upcoming projects.",
    category: "meeting",
    priority: "high",
    timestamp: "10:32 AM",
  },
  {
    id: "2",
    sender: "GitHub",
    senderEmail: "notifications@github.com",
    subject: "New pull request on cloudmail-api",
    summary: "User @devteam has opened a new pull request #142 for the authentication module updates.",
    category: "work",
    priority: "medium",
    timestamp: "9:45 AM",
  },
  {
    id: "3",
    sender: "Michael Chen",
    senderEmail: "m.chen@partner.org",
    subject: "Partnership Proposal Follow-up",
    summary: "Following up on our discussion about the strategic partnership. Attached are the revised terms.",
    category: "work",
    priority: "high",
    timestamp: "9:12 AM",
  },
  {
    id: "4",
    sender: "TechNews Daily",
    senderEmail: "digest@technews.com",
    subject: "Your Daily Tech Digest",
    summary: "Top stories: AI advances in email processing, Cloud computing trends, and cybersecurity updates.",
    category: "newsletter",
    priority: "low",
    timestamp: "8:00 AM",
  },
  {
    id: "5",
    sender: "HR Department",
    senderEmail: "hr@company.com",
    subject: "Updated PTO Policy",
    summary: "Please review the updated paid time off policy effective next quarter. Action required by Friday.",
    category: "work",
    priority: "medium",
    timestamp: "Yesterday",
  },
  {
    id: "6",
    sender: "Alex Rivera",
    senderEmail: "alex.r@team.io",
    subject: "Sprint Planning Session",
    summary: "Reminder: Sprint planning session tomorrow at 2 PM. Please come prepared with your backlog items.",
    category: "meeting",
    priority: "medium",
    timestamp: "Yesterday",
  },
  {
    id: "7",
    sender: "Amazon Web Services",
    senderEmail: "no-reply@aws.amazon.com",
    subject: "Monthly Usage Report",
    summary: "Your AWS usage report for the previous month is now available. Total charges: $1,234.56",
    category: "work",
    priority: "low",
    timestamp: "Yesterday",
  },
]

const categoryColors: Record<Email["category"], string> = {
  work: "bg-primary/20 text-primary border-primary/30",
  meeting: "bg-status-info/20 text-status-info border-status-info/30",
  personal: "bg-status-success/20 text-status-success border-status-success/30",
  newsletter: "bg-muted text-muted-foreground border-border",
  spam: "bg-status-danger/20 text-status-danger border-status-danger/30",
}

const priorityColors: Record<Email["priority"], string> = {
  high: "bg-status-danger/20 text-status-danger border-status-danger/30",
  medium: "bg-status-warning/20 text-status-warning border-status-warning/30",
  low: "bg-status-success/20 text-status-success border-status-success/30",
}

interface EmailTableProps {
  categoryFilter?: string
  priorityFilter?: string
  searchQuery?: string
}

export function EmailTable({ categoryFilter, priorityFilter, searchQuery }: EmailTableProps) {
  const filteredEmails = sampleEmails.filter((email) => {
    if (categoryFilter && categoryFilter !== "all" && email.category !== categoryFilter) {
      return false
    }
    if (priorityFilter && priorityFilter !== "all" && email.priority !== priorityFilter) {
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
    <div className="rounded-lg border border-border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sender</TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Subject</TableHead>
            <TableHead className="hidden text-xs font-semibold uppercase tracking-wider text-muted-foreground lg:table-cell">Summary</TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Category</TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Priority</TableHead>
            <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredEmails.map((email, index) => (
            <TableRow
              key={email.id}
              className={cn(
                "cursor-pointer border-border transition-colors hover:bg-muted/50",
                index % 2 === 0 && "bg-muted/20"
              )}
            >
              <TableCell className="py-4">
                <div className="flex flex-col">
                  <span className="font-medium text-foreground">{email.sender}</span>
                  <span className="text-xs text-muted-foreground">{email.senderEmail}</span>
                </div>
              </TableCell>
              <TableCell className="max-w-[200px] py-4">
                <span className="line-clamp-1 font-medium text-foreground">{email.subject}</span>
              </TableCell>
              <TableCell className="hidden max-w-[300px] py-4 lg:table-cell">
                <span className="line-clamp-2 text-sm text-muted-foreground">{email.summary}</span>
              </TableCell>
              <TableCell className="py-4">
                <Badge variant="outline" className={cn("text-xs capitalize", categoryColors[email.category])}>
                  {email.category}
                </Badge>
              </TableCell>
              <TableCell className="py-4">
                <Badge variant="outline" className={cn("text-xs capitalize", priorityColors[email.priority])}>
                  {email.priority}
                </Badge>
              </TableCell>
              <TableCell className="py-4 text-right text-sm text-muted-foreground">
                {email.timestamp}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
