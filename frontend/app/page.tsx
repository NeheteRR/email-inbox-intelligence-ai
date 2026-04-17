"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Navbar } from "@/components/dashboard/navbar"
import { StatsCards, DashboardStats } from "@/components/dashboard/stats-cards"
import { Filters } from "@/components/dashboard/filters"
import { EmailTable, Email } from "@/components/dashboard/email-table"
import { EmailDetails } from "@/components/dashboard/email-details"
import { AIInsights, InsightData } from "@/components/dashboard/ai-insights"

import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

export default function Dashboard() {
  const [activeItem, setActiveItem] = useState("dashboard")
  const [categoryFilter, setCategoryFilter] = useState<string>()
  const [priorityFilter, setPriorityFilter] = useState<string>()
  const [searchQuery, setSearchQuery] = useState<string>()
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)

  const [emails, setEmails] = useState<Email[]>([])
  const [statsData, setStatsData] = useState<DashboardStats | null>(null)
  const [insightsData, setInsightsData] = useState<InsightData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sync sidebar navigation with dashboard filters
  useEffect(() => {
    switch (activeItem) {
      case "dashboard":
      case "all-emails":
        setCategoryFilter("all")
        setPriorityFilter("all")
        break
      case "priority":
        setCategoryFilter("all")
        setPriorityFilter("high")
        break
      case "meetings":
        setCategoryFilter("meetings")
        setPriorityFilter("all")
        break
      // Handle other cases explicitly if needed
    }
  }, [activeItem])

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [emailsRes, statsRes] = await Promise.all([
        fetch("http://localhost:8000/emails"),
        fetch("http://localhost:8000/dashboard-stats")
      ])

      if (!emailsRes.ok || !statsRes.ok) {
        throw new Error("Failed to fetch data from backend")
      }

      const emailsData = await emailsRes.json()
      const statsObj = await statsRes.json()

      const processedEmails = (emailsData.emails || []).map((email: any) => {
        let senderName = email.sender
        let senderEmail = ""
        
        if (email.sender && email.sender.includes("<") && email.sender.includes(">")) {
          const matches = email.sender.match(/(.*)<(.*)>/)
          if (matches) {
            senderName = matches[1].trim()
            senderEmail = matches[2].trim()
          }
        }

        let displayTime = "Recently"
        if (email.received_at) {
          try {
            const d = new Date(email.received_at)
            if (!isNaN(d.getTime())) {
              displayTime = d.toLocaleString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit'
              })
            } else {
              displayTime = email.received_at
            }
          } catch (e) {
            displayTime = email.received_at
          }
        }

        return {
          ...email,
          sender: senderName || "Unknown Sender",
          senderEmail: senderEmail || (email.sender.includes("@") ? email.sender : "Unknown Email"),
          timestamp: displayTime, 
        }
      })

      setEmails(processedEmails)
      setStatsData(statsObj.stats)
      setInsightsData(statsObj.insights)

    } catch (err: any) {
      console.error(err)
      setError(err.message || "An error occurred while loading data.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleViewUrgent = () => {
    setPriorityFilter("high")
  }

  const handleEmailModified = async () => {
    await fetchData()
  }

  const handleSyncLatest = async () => {
    try {
      setIsSyncing(true)
      const res = await fetch("http://localhost:8000/process-emails")
      if (!res.ok) throw new Error("Failed to sync new emails")
      
      const data = await res.json()
      if (data.processed > 0) {
        toast.success(`Successfully analyzed ${data.processed} new emails`)
      } else {
        toast.info("No new emails to process")
      }
      
      await fetchData()
    } catch (e) {
      console.error(e)
      toast.error("Failed to sync latest emails")
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div className="h-screen w-full bg-background flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar activeItem={activeItem} onItemClick={setActiveItem} />

      {/* Main content */}
      <div className="flex-1 flex flex-col pl-64 overflow-hidden">
        <Navbar />

        <main className="p-6 flex-1 flex flex-col overflow-hidden">
          <div className="mx-auto w-full 2xl:max-w-[1600px] flex-1 flex flex-col min-h-0">
            {isLoading && emails.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  <p className="text-sm text-muted-foreground">Loading dashboard data...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-2 rounded-lg border border-status-danger/30 bg-status-danger/10 p-6 text-center">
                  <p className="font-medium text-status-danger">Error Loading Data</p>
                  <p className="text-sm text-status-danger/80">{error}</p>
                  <button 
                    onClick={() => window.location.reload()}
                    className="mt-4 rounded-md bg-status-danger px-4 py-2 text-sm font-medium text-white hover:bg-status-danger/90 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Stats Cards Header & Action */}
                <div className="flex items-center justify-between mb-4 shrink-0">
                  <h2 className="text-lg font-semibold tracking-tight text-foreground">Overview</h2>
                  <Button 
                    onClick={handleSyncLatest} 
                    disabled={isSyncing} 
                    className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <RefreshCw className={cn("h-4 w-4", isSyncing && "animate-spin")} />
                    {isSyncing ? "Syncing (may take a minute)..." : "Sync Latest Emails"}
                  </Button>
                </div>

                {/* Stats Cards */}
                <section className="mb-6 shrink-0">
                  <StatsCards statsData={statsData} />
                </section>

                {/* Main Content Grid */}
                <div className="grid gap-6 lg:grid-cols-[1fr_360px] flex-1 min-h-0 min-w-0">
                  {/* Left Column - Filters & Table */}
                  <div className="flex flex-col gap-4 min-w-0 flex-1 overflow-hidden">
                    <div className="shrink-0">
                      <Filters
                        emails={emails}
                        activeCategory={categoryFilter || "all"}
                        onCategoryChange={setCategoryFilter}
                        onPriorityChange={setPriorityFilter}
                        onSearchChange={setSearchQuery}
                      />
                    </div>
                    <div className="flex-1 overflow-hidden flex flex-col min-h-0 rounded-lg border border-border bg-card">
                      <div className="flex-1 overflow-y-auto">
                        <EmailTable
                          emails={emails}
                          categoryFilter={categoryFilter}
                          priorityFilter={priorityFilter}
                          searchQuery={searchQuery}
                          selectedEmailId={selectedEmail?.id}
                          onEmailSelect={setSelectedEmail}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Right Column - AI Insights / Email Details */}
                  <div className="h-full overflow-hidden">
                    {selectedEmail ? (
                      <EmailDetails 
                        email={selectedEmail} 
                        onClose={() => setSelectedEmail(null)}
                        onEmailModified={handleEmailModified}
                      />
                    ) : (
                      <AIInsights 
                        insightsData={insightsData}
                        totalEmails={statsData?.total_emails || 0}
                        urgentCount={statsData?.high_priority || 0}
                        onViewUrgent={handleViewUrgent}
                      />
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
