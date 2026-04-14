"use client"

import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search } from "lucide-react"

interface FiltersProps {
  onCategoryChange?: (value: string) => void
  onPriorityChange?: (value: string) => void
  onSearchChange?: (value: string) => void
}

export function Filters({ onCategoryChange, onPriorityChange, onSearchChange }: FiltersProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      {/* Category Filter */}
      <Select onValueChange={onCategoryChange} defaultValue="all">
        <SelectTrigger className="w-full bg-input sm:w-[160px]">
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          <SelectItem value="work">Work</SelectItem>
          <SelectItem value="meeting">Meeting</SelectItem>
          <SelectItem value="personal">Personal</SelectItem>
          <SelectItem value="newsletter">Newsletter</SelectItem>
          <SelectItem value="spam">Spam</SelectItem>
        </SelectContent>
      </Select>

      {/* Priority Filter */}
      <Select onValueChange={onPriorityChange} defaultValue="all">
        <SelectTrigger className="w-full bg-input sm:w-[140px]">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Priority</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
        </SelectContent>
      </Select>

      {/* Search */}
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by sender or subject..."
          className="bg-input pl-9"
          onChange={(e) => onSearchChange?.(e.target.value)}
        />
      </div>
    </div>
  )
}
