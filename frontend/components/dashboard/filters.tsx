"use client"

import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  Search, 
  Inbox, 
  Calendar, 
  PartyPopper, 
  CheckSquare, 
  RefreshCcw, 
  FileText, 
  Book, 
  CreditCard, 
  Megaphone, 
  MoreHorizontal,
  SlidersHorizontal
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Email } from "./email-table"

interface FiltersProps {
  emails?: Email[]
  activeCategory?: string
  onCategoryChange?: (value: string) => void
  onPriorityChange?: (value: string) => void
  onSearchChange?: (value: string) => void
}

export function Filters({ emails = [], activeCategory = "all", onCategoryChange, onPriorityChange, onSearchChange }: FiltersProps) {
  
  const counts = emails.reduce((acc, email) => {
    const cat = (email.category || "other").toLowerCase()
    acc[cat] = (acc[cat] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  // Mapping categories to match the screenshots
  const categories = [
    { id: "all", label: "All", icon: Inbox, count: emails.length },
    { id: "meetings", label: "Meetings", icon: Calendar, count: counts["meetings"] || counts["meeting"] || 0 },
    { id: "events", label: "Events", icon: PartyPopper, count: counts["events"] || 0 },
    { id: "tasks", label: "Tasks", icon: CheckSquare, count: counts["tasks"] || counts["work"] || 0 },
    { id: "follow-ups", label: "Follow-ups", icon: RefreshCcw, count: counts["follow-ups"] || 0 },
    { id: "reports", label: "Reports", icon: FileText, count: counts["reports"] || 0 },
    { id: "references", label: "References", icon: Book, count: counts["references"] || counts["personal"] || 0 },
    { id: "finance", label: "Finance", icon: CreditCard, count: counts["finance"] || 0 },
    { id: "promotions", label: "Promotions", icon: Megaphone, count: counts["promotions"] || 0 },
    { id: "other", label: "Other", icon: MoreHorizontal, count: counts["spam"] || counts["other"] || 0 },
  ]

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Category Pills Row */}
      <div className="flex w-full items-center gap-2 overflow-x-auto rounded-xl bg-card border border-border p-2 shadow-sm [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {categories.map((cat) => {
          const isActive = activeCategory === cat.id
          const Icon = cat.icon
          return (
            <button
              key={cat.id}
              onClick={() => onCategoryChange?.(cat.id)}
              className={cn(
                "flex items-center whitespace-nowrap shrink-0 gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted/80",
                isActive 
                  ? "bg-blue-500 text-white hover:bg-blue-600" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {cat.label}
              {cat.count > 0 && (
                <span className={cn(
                  "flex h-5 items-center justify-center rounded-full px-2 text-xs",
                  isActive ? "bg-white/20 text-white" : "bg-muted text-muted-foreground"
                )}>
                  {cat.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Priority and Search Row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative">
          <Select onValueChange={onPriorityChange} defaultValue="all">
            <SelectTrigger className="w-full bg-input sm:w-[160px] pl-9 border-blue-500/30 hover:border-blue-500/50">
              <SlidersHorizontal className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <SelectValue placeholder="All Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priority</SelectItem>
              <SelectItem value="high">High Priority</SelectItem>
              <SelectItem value="medium">Medium Priority</SelectItem>
              <SelectItem value="low">Low Priority</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search emails..."
            className="bg-input pl-9 rounded-lg"
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
        </div>
      </div>
    </div>
  )
}
