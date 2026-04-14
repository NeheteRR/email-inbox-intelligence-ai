"use client"

import { useState } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Navbar } from "@/components/dashboard/navbar"
import { StatsCards } from "@/components/dashboard/stats-cards"
import { Filters } from "@/components/dashboard/filters"
import { EmailTable } from "@/components/dashboard/email-table"
import { AIInsights } from "@/components/dashboard/ai-insights"

export default function Dashboard() {
  const [activeItem, setActiveItem] = useState("dashboard")
  const [categoryFilter, setCategoryFilter] = useState<string>()
  const [priorityFilter, setPriorityFilter] = useState<string>()
  const [searchQuery, setSearchQuery] = useState<string>()

  return (
    <div className="min-h-screen w-full bg-background flex">
      {/* Sidebar */}
      <Sidebar activeItem={activeItem} onItemClick={setActiveItem} />

      {/* Main content */}
      <div className="flex-1 pl-64">
        <Navbar />

        <main className="p-6">
          <div className="mx-auto w-full 2xl:max-w-[1600px]">
            {/* Stats Cards */}
            <section className="mb-6">
              <StatsCards />
            </section>

            {/* Main Content Grid */}
            <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
              {/* Left Column - Filters & Table */}
              <div className="flex flex-col gap-4">
                <Filters
                  onCategoryChange={setCategoryFilter}
                  onPriorityChange={setPriorityFilter}
                  onSearchChange={setSearchQuery}
                />
                <EmailTable
                  categoryFilter={categoryFilter}
                  priorityFilter={priorityFilter}
                  searchQuery={searchQuery}
                />
              </div>

              {/* Right Column - AI Insights */}
              <div className="lg:sticky lg:top-20 lg:h-fit">
                <AIInsights />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
