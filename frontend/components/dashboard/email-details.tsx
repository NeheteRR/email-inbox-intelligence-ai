import { X, Reply, Forward, Star, Archive, Trash2, User, Sparkles, Loader2 } from "lucide-react"
import { Email } from "./email-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

interface EmailDetailsProps {
  email: Email
  onClose: () => void
  onEmailModified?: () => void
}

export function EmailDetails({ email, onClose, onEmailModified }: EmailDetailsProps) {
  // Modals state
  const [isReplyOpen, setIsReplyOpen] = useState(false)
  const [isForwardOpen, setIsForwardOpen] = useState(false)
  
  // Reply State
  const [replyText, setReplyText] = useState("")
  const [isSendingReply, setIsSendingReply] = useState(false)
  
  // AI Suggestions State
  const [aiSuggestions, setAiSuggestions] = useState<any[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  // Forward State
  const [forwardEmailTo, setForwardEmailTo] = useState("")
  const [forwardNote, setForwardNote] = useState("")
  const [isForwarding, setIsForwarding] = useState(false)

  // Extract initials for the avatar if name is available, otherwise default
  let initials = "U"
  if (email.sender && email.sender !== "Unknown Sender") {
    initials = email.sender.substring(0, 2).toUpperCase()
  }

  // Define Category Styling
  const getCategoryTheme = (category: string) => {
    switch (category?.toLowerCase()) {
      case "promotions":
      case "promotion":
        return "bg-pink-500/10 text-pink-500 border-pink-500/20"
      case "finance":
        return "bg-green-500/10 text-green-500 border-green-500/20"
      case "meetings":
      case "events":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20"
      default:
        return "bg-secondary text-secondary-foreground"
    }
  }

  // Generate AI Reply
  const handleGenerateReply = async () => {
    setIsGenerating(true)
    setAiSuggestions([])
    try {
      const res = await fetch("http://localhost:8000/generate-reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_body: email.summary || email.subject, // fallback to summary or subject
          category: email.category || "References",
          variations: 2
        })
      })
      if (!res.ok) throw new Error("Failed to generate")
      const data = await res.json()
      if (data.variations) {
        setAiSuggestions(data.variations)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsGenerating(false)
    }
  }

  // API Call handlers
  const handleReplySubmit = async () => {
    if (!replyText.trim()) return
    setIsSendingReply(true)
    try {
      const res = await fetch("http://localhost:8000/reply-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          to: email.senderEmail, 
          subject: `Re: ${email.subject}`, 
          body: replyText, 
          thread_id: (email as any).gmail_thread_id || null 
        }),
      })
      if (!res.ok) throw new Error("Failed to send reply")
      
      setIsReplyOpen(false)
      setReplyText("")
      onEmailModified?.()
    } catch (e) {
      console.error(e)
    } finally {
      setIsSendingReply(false)
    }
  }

  const handleForwardSubmit = async () => {
    if (!forwardEmailTo.trim()) return
    setIsForwarding(true)
    try {
      const res = await fetch("http://localhost:8000/forward-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message_id: (email as any).gmail_message_id || (email as any).id, 
          to: forwardEmailTo, 
          note: forwardNote 
        }),
      })
      if (!res.ok) throw new Error("Failed to forward email")
      
      setIsForwardOpen(false)
      setForwardEmailTo("")
      setForwardNote("")
      onEmailModified?.()
    } catch (e) {
      console.error(e)
    } finally {
      setIsForwarding(false)
    }
  }

  const handleModify = async (action: string) => {
    try {
      const res = await fetch("http://localhost:8000/modify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: (email as any).gmail_message_id || (email as any).id || "mock-id", action }),
      })
      if (!res.ok) throw new Error("Failed to modify email")
      
      toast.success(`Email marked as ${action}`)
      
      if (action === "archive" || action === "delete") {
        onClose()
        onEmailModified?.()
      } else {
        // Just trigger refresh but dont close panel for star, unread etc
        onEmailModified?.()
      }
    } catch (e) {
      console.error(e)
      toast.error(`Failed to ${action} email`)
    }
  }

  return (
    <>
      <div className="flex h-full flex-col rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border p-5">
          <h2 className="text-xl font-bold leading-tight text-foreground line-clamp-2 pr-4">
            {email.subject}
          </h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground shrink-0"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
          {/* Sender Info */}
          <div className="flex items-center gap-4 mb-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-500 shrink-0 uppercase font-semibold">
              {initials}
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="font-semibold text-foreground truncate">{email.sender}</span>
              <span className="text-sm text-muted-foreground truncate">{email.senderEmail}</span>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-y-6 gap-x-4 border-b border-border pb-6 mb-6">
            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold tracking-wider text-muted-foreground flex items-center gap-1.5 uppercase">
                <span className="opacity-70">🏷️</span> Category
              </span>
              <div>
                <Badge variant="outline" className={cn("font-medium", getCategoryTheme(email.category))}>
                  {email.category || "Uncategorized"}
                </Badge>
              </div>
            </div>
            
            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold tracking-wider text-muted-foreground flex items-center gap-1.5 uppercase">
                <span className="opacity-70">⚡</span> Priority
              </span>
              <div className="flex items-center gap-2">
                <span className={cn(
                  "h-2 w-2 rounded-full",
                  email.priority?.toLowerCase() === "high" ? "bg-status-danger" :
                  email.priority?.toLowerCase() === "medium" ? "bg-status-warning" : "bg-status-success"
                )} />
                <span className={cn(
                  "text-sm font-medium",
                  email.priority?.toLowerCase() === "high" ? "text-status-danger" :
                  email.priority?.toLowerCase() === "medium" ? "text-status-warning" : "text-status-success"
                )}>
                  {email.priority || "Low"}
                </span>
              </div>
            </div>

            <div className="col-span-2 flex flex-col gap-2">
              <span className="text-xs font-semibold tracking-wider text-muted-foreground flex items-center gap-1.5 uppercase">
                <span className="opacity-70">🕒</span> Received
              </span>
              <span className="text-sm font-medium text-foreground">{email.timestamp}</span>
            </div>
          </div>

          {/* AI Summary */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-semibold tracking-wider text-muted-foreground uppercase flex items-center gap-1.5">
              <span className="opacity-70">✨</span> AI Summary
            </span>
            <p className="text-sm leading-relaxed text-foreground/90">
              {email.summary}
            </p>
          </div>
        </div>

        {/* Action Footer */}
        <div className="border-t border-border p-4 bg-muted/20 shrink-0">
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="default" onClick={() => setIsReplyOpen(true)} className="bg-blue-600 hover:bg-blue-700 text-white gap-2 h-9 px-4 rounded-full">
              <Reply className="h-4 w-4" />
              Reply
            </Button>
            <Button variant="secondary" onClick={() => setIsForwardOpen(true)} className="gap-2 h-9 px-4 rounded-full hover:bg-secondary/80">
              <Forward className="h-4 w-4" />
              Forward
            </Button>
            <Button variant="secondary" onClick={() => handleModify("star")} className="gap-2 h-9 px-4 rounded-full hover:bg-secondary/80">
              <Star className="h-4 w-4" />
              Star
            </Button>
            <Button variant="secondary" onClick={() => handleModify("archive")} className="gap-2 h-9 px-4 rounded-full hover:bg-secondary/80">
              <Archive className="h-4 w-4" />
              Archive
            </Button>
            <div className="flex-1" />
            <Button variant="ghost" onClick={() => handleModify("delete")} className="text-status-danger hover:text-status-danger hover:bg-status-danger/10 gap-2 h-9 px-4 rounded-full">
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Reply Dialog */}
      <Dialog open={isReplyOpen} onOpenChange={setIsReplyOpen}>
        <DialogContent className="sm:max-w-[750px] w-[90vw] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Reply to {email.sender}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-4">
            
            {/* AI Suggestion Generator */}
            <div className="flex flex-col gap-3 rounded-lg border border-purple-500/20 bg-purple-500/5 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold text-purple-400">
                  <Sparkles className="h-4 w-4" />
                  AI Reply Suggestions
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={handleGenerateReply}
                  disabled={isGenerating}
                  className="h-8 gap-2 border-purple-500/30 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300"
                >
                  {isGenerating ? <Loader2 className="h-3 w-3 animate-spin"/> : "Generate"}
                </Button>
              </div>

              {aiSuggestions.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
                  {aiSuggestions.map((sug, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => setReplyText(sug.reply)}
                      className="cursor-pointer rounded-md border border-border bg-card p-4 text-sm text-muted-foreground transition-colors hover:border-purple-500/50 hover:bg-purple-500/5 shadow-sm"
                    >
                      <span className="font-semibold text-purple-300 mb-2 block">{sug.label}</span>
                      <span className="line-clamp-3">{sug.reply}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid gap-2 mt-2">
              <Label htmlFor="reply-message" className="text-base">Your Message</Label>
              <Textarea 
                id="reply-message" 
                rows={8} 
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply here..." 
                className="resize-none text-base p-4"
              />
            </div>
          </div>
          <DialogFooter className="pt-4 border-t border-border/50">
            <Button variant="outline" onClick={() => setIsReplyOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleReplySubmit} 
              disabled={!replyText.trim() || isSendingReply}
              className="bg-blue-600 hover:bg-blue-700 text-white gap-2 px-6"
            >
              {isSendingReply ? <Loader2 className="h-4 w-4 animate-spin" /> : <Reply className="h-4 w-4" />}
              Send Reply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Forward Dialog */}
      <Dialog open={isForwardOpen} onOpenChange={setIsForwardOpen}>
        <DialogContent className="sm:max-w-[600px] w-[90vw]">
          <DialogHeader>
            <DialogTitle>Forward Email</DialogTitle>
          </DialogHeader>
          <div className="grid gap-5 py-4">
            <div className="grid gap-2">
              <Label htmlFor="forward-to" className="text-base">To</Label>
              <Input 
                id="forward-to" 
                type="email" 
                value={forwardEmailTo}
                onChange={(e) => setForwardEmailTo(e.target.value)}
                placeholder="colleague@company.com" 
                className="text-base h-11"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="forward-note" className="text-base">Personal Note (Optional)</Label>
              <Textarea 
                id="forward-note" 
                rows={4}
                value={forwardNote}
                onChange={(e) => setForwardNote(e.target.value)}
                placeholder="FYI, I thought you should see this..." 
                className="resize-none text-base p-3"
              />
            </div>
          </div>
          <DialogFooter className="pt-4 border-t border-border/50">
            <Button variant="outline" onClick={() => setIsForwardOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleForwardSubmit}
              disabled={!forwardEmailTo.trim() || isForwarding}
              className="px-6 gap-2"
            >
              {isForwarding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Forward className="h-4 w-4" />}
              Forward Message
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
