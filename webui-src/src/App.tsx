import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Plus,
  CheckCircle2,
  BookOpen,
  Folder,
  FileText,
  Link2,
  Menu,
  Search,
  HelpCircle,
  Home,
  MoreHorizontal,
  Play,
  X,
  Sparkles,
  Paperclip,
  Mic,
  ChevronRight,
  Activity,
  Circle,
  ArrowRight,
} from 'lucide-react'

// NOVA brand mark
function NovaMark({ small = false }: { small?: boolean }) {
  return (
    <svg
      aria-hidden="true"
      className={small ? 'nova-mark nova-mark-small' : 'nova-mark'}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 1.5 15.2 8.8 22.5 12l-7.3 3.2L12 22.5l-3.2-7.3L1.5 12l7.3-3.2L12 1.5Z"
        fill="currentColor"
      />
    </svg>
  )
}

// API client for Orville backend (proxied by Vite dev server)

interface Run {
  run_id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  updated_at: string
}

interface TasksResponse {
  runs: Run[]
}

async function fetchTasks(): Promise<Run[]> {
  const res = await fetch('/api/v1/runs')
  if (!res.ok) throw new Error('Failed to fetch tasks')
  const data: TasksResponse = await res.json()
  return data.runs
}

const navigation = [
  { label: 'New task', icon: Plus },
  { label: 'Tasks', icon: CheckCircle2 },
  { label: 'Deep Research', icon: BookOpen },
  { label: 'Projects', icon: Folder },
  { label: 'Files', icon: FileText },
  { label: 'Connectors', icon: Link2 },
]

const starterPrompts = [
  { label: 'Research a topic', icon: Search },
  { label: 'Analyze my data', icon: Activity },
  { label: 'Draft a document', icon: FileText },
  { label: 'Find and summarize', icon: Search },
]

function relativeTime(value: string) {
  const date = new Date(value)
  const elapsed = Date.now() - date.getTime()
  if (!Number.isFinite(elapsed) || elapsed < 60_000) return 'Just now'
  const minutes = Math.floor(elapsed / 60_000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function statusLabel(status: Run['status']) {
  if (status === 'running') return 'In progress'
  return status.charAt(0).toUpperCase() + status.slice(1)
}

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [search, setSearch] = useState('')
  const [activeNav, setActiveNav] = useState('New task')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [activityOpen, setActivityOpen] = useState(true)

  const [tasks, setTasks] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // Fetch tasks on mount
  useEffect(() => {
    fetchTasks()
      .then(setTasks)
      .catch((err) => {
        console.error('Failed to load tasks:', err)
        toast.error('Could not load tasks')
      })
      .finally(() => setLoading(false))
  }, [])

  const filteredTasks = search
    ? tasks.filter((t) => t.title.toLowerCase().includes(search.toLowerCase()))
    : tasks

  const currentTask = tasks.find((t) => t.status === 'running') ?? tasks[0]

  const handleNavigate = (label: string) => {
    setActiveNav(label)
    setMobileNavOpen(false)
  }

  const startTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) {
      toast.error('Tell Orville what you need', {
        description: 'Add a task description to get started.',
      })
      return
    }
    setSubmitting(true)
    try {
      const res = await fetch('/api/v1/objectives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective: prompt,
          generation_mode: 'code',
          privacy_class: 'cloud_approved',
          review_before_execution: true,
        }),
      })
      if (!res.ok) throw new Error('Failed to create task')
      await res.json() // consume response
      toast.success('Task created', { description: 'Review the plan and approve to run.' })
      // Refresh tasks
      const updated = await fetchTasks()
      setTasks(updated)
      setPrompt('')
    } catch (err) {
      toast.error('Task creation failed', { description: String(err) })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="workspace-shell">
      {/* Mobile nav scrim */}
      {mobileNavOpen && (
        <button
          className="nav-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
        <div className="brand-row">
          <div className="brand-lockup" aria-label="Orville home">
            <NovaMark />
            <span>Orville</span>
          </div>
          <button
            className="icon-button mobile-close"
            aria-label="Close navigation"
            onClick={() => setMobileNavOpen(false)}
          >
            <X size={19} />
          </button>
        </div>
        <nav className="primary-nav" aria-label="Primary navigation">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              className={`nav-item ${activeNav === label ? 'nav-item-active' : ''}`}
              key={label}
              onClick={() => handleNavigate(label)}
              aria-current={activeNav === label ? 'page' : undefined}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="workspace-switcher" onClick={() => toast('Personal workspace')}>
            <span className="workspace-home">
              <Home size={20} strokeWidth={1.8} />
            </span>
            <span className="workspace-label">Personal workspace</span>
            <ChevronRight size={17} className="muted-icon" />
          </button>
          <button className="profile-row" onClick={() => toast('Profile')}>
            <span className="avatar avatar-photo">U</span>
            <span className="profile-copy">
              <strong>User</strong>
              <small>Local operator</small>
            </span>
            <MoreHorizontal size={19} className="muted-icon" />
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="app-column">
        {/* Top bar */}
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMobileNavOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumbs">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{activeNav === 'New task' ? 'Home' : activeNav}</strong>
          </div>
          <div className="topbar-actions">
            <label className="global-search">
              <Search size={17} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search anything..."
                aria-label="Search recent tasks"
              />
              {!search && (
                <span className="shortcut">
                  <span aria-hidden="true">⌘</span> K
                </span>
              )}
              {search && (
                <button
                  type="button"
                  className="search-clear"
                  aria-label="Clear search"
                  onClick={() => setSearch('')}
                >
                  <X size={14} />
                </button>
              )}
            </label>
            <button className="icon-button help-button" aria-label="Help">
              <HelpCircle size={21} strokeWidth={1.8} />
            </button>
            <button className="avatar avatar-top" aria-label="User profile">
              U
            </button>
          </div>
        </header>

        {/* Dashboard */}
        <div className="dashboard-grid">
          <main className="main-content">
            <section className="welcome-block">
              <p className="eyebrow">
                <span className="eyebrow-dot" /> YOUR PERSONAL WORKSPACE
              </p>
              <h1>Good afternoon</h1>
              <p className="welcome-subtitle">What would you like to work on?</p>
            </section>

            {/* Composer */}
            <form className="composer-card" onSubmit={startTask}>
              <div className="composer-topline">
                <span className="composer-sparkle">
                  <Sparkles size={18} fill="currentColor" />
                </span>
                <span className="composer-caption">A little direction goes a long way.</span>
              </div>
              <label className="sr-only" htmlFor="task-prompt">Describe a task for Orville</label>
              <textarea
                id="task-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe a task, and Orville will take it from here..."
                rows={2}
                maxLength={4000}
              />
              <div className="composer-footer">
                <div className="composer-tools">
                  <button type="button" className="tool-button" aria-label="Add option">
                    <Plus size={19} />
                  </button>
                  <button type="button" className="tool-button" aria-label="Attach file" onClick={() => toast('File attachment coming soon')}>
                    <Paperclip size={18} />
                  </button>
                  <button type="button" className="tool-button" aria-label="Voice input" onClick={() => toast('Voice input coming soon')}>
                    <Mic size={18} />
                  </button>
                  <span className="composer-hint">Enter to start · Shift + Enter for new line</span>
                </div>
                <button className="start-button" type="submit" disabled={submitting}>
                  <Play size={15} fill="currentColor" />
                  <span>{submitting ? 'Saving…' : 'Start task'}</span>
                </button>
              </div>
            </form>

            {/* Starter prompts */}
            <div className="suggestion-row" aria-label="Suggested tasks">
              {starterPrompts.map(({ label, icon: Icon }) => (
                <button
                  className="suggestion-chip"
                  key={label}
                  onClick={() => setPrompt((p) => (p ? `${p} — ${label.toLowerCase()}` : `${label}: `))}
                >
                  <Icon size={14} strokeWidth={1.8} />
                  <span>{label}</span>
                </button>
              ))}
            </div>

            {/* Recent tasks */}
            <section className="recent-section">
              <div className="section-heading">
                <div>
                  <h2>Recent tasks</h2>
                  <span className="section-count">
                    {filteredTasks.length} {filteredTasks.length === 1 ? 'task' : 'tasks'}
                  </span>
                </div>
                <button className="text-button" onClick={() => handleNavigate('Tasks')}>
                  View all <ArrowRight size={15} />
                </button>
              </div>
              <div className="task-list">
                {loading ? (
                  <div className="empty-state" role="status">
                    <Circle size={19} />
                    <strong>Loading workspace tasks</strong>
                    <span>Checking your saved tasks and activity.</span>
                  </div>
                ) : filteredTasks.length ? (
                  filteredTasks.map((task) => (
                    <article className="task-row" key={task.run_id}>
                      <button className="task-open" aria-label={`Open ${task.title}`}>
                        <span className="task-glyph">
                          <FileText size={21} strokeWidth={1.8} />
                        </span>
                        <span className="task-copy">
                          <strong>{task.title}</strong>
                          <small>{task.status}</small>
                        </span>
                      </button>
                      <span className="task-time">{relativeTime(task.updated_at)}</span>
                      <span className={`status-pill status-${task.status}`}>
                        <span className="status-dot" />
                        {statusLabel(task.status)}
                      </span>
                      <button className="row-more" aria-label="More actions">
                        <MoreHorizontal size={18} />
                      </button>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">
                    <Search size={19} />
                    <strong>Your task list is ready</strong>
                    <span>Describe a task above and it will be saved here.</span>
                  </div>
                )}
              </div>
            </section>
          </main>

          {/* Activity panel */}
          <aside className={`activity-panel ${activityOpen ? 'activity-panel-open' : ''}`} aria-label="Task activity">
            <div className="activity-panel-heading">
              <div>
                <span className="activity-overline">WORKSPACE RUN</span>
                <h2>Task activity</h2>
              </div>
              <button className="icon-button panel-close" aria-label="Close" onClick={() => setActivityOpen(false)}>
                <X size={18} />
              </button>
            </div>
            {currentTask ? (
              <div className="run-card">
                <div className="run-topline">
                  <span className="run-icon">
                    <Activity size={18} />
                  </span>
                  <div className="run-title-group">
                    <strong>{currentTask.title}</strong>
                    <span>Interactive task workflow</span>
                  </div>
                  <span className="run-badge">
                    <i /> {statusLabel(currentTask.status)}
                  </span>
                </div>
                <button className="task-detail-button task-detail-button-primary" onClick={() => toast('Task details')}>
                  <Plus size={14} /> Open task details
                </button>
              </div>
            ) : (
              <div className="run-card activity-empty">
                <span className="run-icon">
                  <Activity size={18} />
                </span>
                <strong>No active task yet</strong>
                <p>Saved run steps and activity will appear here once you start a task.</p>
              </div>
            )}
            <div className="autonomy-note">
              <span className="note-mark">
                <NovaMark small />
              </span>
              <p>
                <strong>Runs start only when requested.</strong>
                <span>Results are saved here.</span>
              </p>
            </div>
            <div className="panel-footer">
              <span className="live-indicator" /> Task runs will appear here
            </div>
          </aside>
        </div>
      </div>

      <button className="mobile-activity-tab" onClick={() => setActivityOpen(true)}>
        <Activity size={16} />
        <span>Task activity</span>
      </button>
    </div>
  )
}