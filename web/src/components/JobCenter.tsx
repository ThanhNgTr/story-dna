import { useQuery } from '@tanstack/react-query'
import { Activity, ExternalLink } from 'lucide-react'
import { Link } from 'react-router'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { api, qk, type Job } from '@/lib/api'
import { JOB_STATUS, STEP_LABEL, fmtDate, fmtDuration, jobProgress } from '@/lib/format'
import { StatusBadge } from './StatusBadge'

function currentStep(job: Job): string | null {
  const running = Object.entries(job.steps).find(([, s]) => s.status === 'running')
  return running ? STEP_LABEL[running[0]] ?? running[0] : null
}

export function JobRow({ job, onNavigate }: { job: Job; onNavigate?: () => void }) {
  const st = JOB_STATUS[job.status]
  const pct = jobProgress(job)
  const step = currentStep(job)
  return (
    <Link to={`/jobs/${job.id}`} onClick={onNavigate}
      className="block rounded-lg border bg-card p-3 transition-colors hover:border-primary/40 hover:bg-accent/40">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 text-sm font-medium leading-snug">{job.title}</div>
        <StatusBadge tone={st.tone}>{st.label}</StatusBadge>
      </div>
      {job.status === 'running' && (
        <div className="mt-2 space-y-1.5">
          {step && <div className="text-xs text-muted-foreground">{step}</div>}
          {pct != null && <Progress value={pct} className="h-1.5" />}
        </div>
      )}
      {job.status === 'failed' && job.error && (
        <div className="mt-1.5 line-clamp-2 text-xs text-destructive">{job.error}</div>
      )}
      <div className="mt-1.5 text-xs text-muted-foreground">
        {fmtDate(job.created_at)}{job.elapsed_sec != null && ` · ${fmtDuration(job.elapsed_sec)}`}
      </div>
    </Link>
  )
}

export function JobCenter() {
  const { data: jobs = [] } = useQuery({ queryKey: qk.jobs, queryFn: () => api.jobs(15) })
  const running = jobs.filter((j) => j.status === 'running')
  const recent = jobs.filter((j) => j.status !== 'running').slice(0, 8)
  return (
    <Sheet>
      <SheetTrigger render={<Button variant={running.length ? 'secondary' : 'ghost'} size="sm" className="gap-2" />}>
        <Activity className={running.length ? 'size-4 animate-pulse text-primary' : 'size-4'} />
        {running.length ? `${running.length} việc đang chạy` : 'Việc'}
      </SheetTrigger>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Việc đang chạy</SheetTitle>
          <SheetDescription>Claude và Codex làm việc nền. Bạn có thể rời trang, xong sẽ có thông báo.</SheetDescription>
        </SheetHeader>
        <div className="space-y-2 px-4">
          {running.length ? running.map((j) => <JobRow key={j.id} job={j} />)
            : <p className="text-sm text-muted-foreground">Không có việc nào đang chạy.</p>}
        </div>
        <div className="mt-6 space-y-2 px-4 pb-6">
          <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Gần đây</div>
          {recent.map((j) => <JobRow key={j.id} job={j} />)}
          <a href="/" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            Tất cả việc (giao diện cũ) <ExternalLink className="size-3" />
          </a>
        </div>
      </SheetContent>
    </Sheet>
  )
}
