import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router'
import { toast } from 'sonner'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { api, qk, type Job, type JobDetail } from '@/lib/api'
import { JOB_STATUS, STEP_LABEL, fmtDate, fmtDuration, fmtEta } from '@/lib/format'

function useLiveJob(id: string) {
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: qk.job(id), queryFn: () => api.job(id) })
  const [log, setLog] = useState<string[]>([])
  useEffect(() => {
    setLog([])
    const es = new EventSource(`/api/jobs/${id}/events`)
    es.addEventListener('job', (ev) => {
      const s: Job = JSON.parse((ev as MessageEvent).data)
      qc.setQueryData<JobDetail>(qk.job(id), (old) => (old ? { ...old, ...s } : old))
    })
    es.addEventListener('log', (ev) => setLog((l) => [...l, ...JSON.parse((ev as MessageEvent).data)].slice(-1500)))
    es.addEventListener('end', () => {
      es.close()
      qc.invalidateQueries({ queryKey: qk.job(id) })
    })
    return () => es.close()
  }, [id, qc])
  return { job: data, log }
}

function StepIcon({ status }: { status: string }) {
  if (status === 'done' || status === 'skipped') return <CheckCircle2 className="size-4 text-success" />
  if (status === 'running') return <Loader2 className="size-4 animate-spin text-primary" />
  if (status === 'failed') return <XCircle className="size-4 text-destructive" />
  return <Circle className="size-4 text-muted-foreground" />
}

export function JobPage() {
  const { id = '' } = useParams()
  const { job, log } = useLiveJob(id)
  const qc = useQueryClient()
  const logRef = useRef<HTMLPreElement>(null)
  const [follow, setFollow] = useState(true)
  useEffect(() => {
    if (follow && logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log, follow])
  const cancel = useMutation({ mutationFn: () => api.cancelJob(id), onError: (e) => toast.error((e as Error).message) })
  const resume = useMutation({
    mutationFn: () => api.resumeJob(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.job(id) }),
    onError: (e) => toast.error((e as Error).message),
  })
  if (!job) return <main className="mx-auto max-w-4xl p-10 text-muted-foreground">Đang tải…</main>
  const st = JOB_STATUS[job.status]
  return (
    <main className="mx-auto max-w-4xl space-y-5 px-4 py-8">
      <div>
        {job.slug && job.session_id && (
          <Link to={`/p/${job.slug}/${job.session_id}`} className="text-xs text-muted-foreground hover:text-foreground">← Về dự án</Link>
        )}
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-semibold">{job.title}</h1>
          <StatusBadge tone={st.tone}>{st.label}</StatusBadge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Bắt đầu {fmtDate(job.started_at ?? job.created_at)}{job.elapsed_sec != null && ` · ${fmtDuration(job.elapsed_sec)}`}
          {job.cost_usd ? ` · ${job.cost_usd.toFixed(2)} USD` : ''}
          {job.status === 'running' && fmtEta(job.eta_sec) && <span className="text-primary"> · {fmtEta(job.eta_sec)}</span>}
        </p>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <ul className="space-y-3">
          {Object.entries(job.steps).map(([name, s]) => (
            <li key={name} className="flex items-start gap-3 text-sm">
              <StepIcon status={s.status} />
              <div className="min-w-0 flex-1">
                <div className={s.status === 'running' ? 'font-medium' : ''}>{STEP_LABEL[name] ?? name}</div>
                {typeof s.total === 'number' && s.total > 0 && (
                  <div className="mt-1.5 flex items-center gap-3">
                    <Progress value={Math.round(100 * (s.done ?? 0) / s.total)} className="h-1.5 flex-1" />
                    <span className="text-xs text-muted-foreground tabular-nums">{s.done ?? 0}/{s.total}{s.failed ? ` · lỗi ${s.failed}` : ''}</span>
                  </div>
                )}
              </div>
            </li>
          ))}
          {!Object.keys(job.steps).length && <li className="text-sm text-muted-foreground">Đang khởi động…</li>}
        </ul>
        {job.error && <p className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">{job.error}</p>}
        <div className="mt-5 flex gap-2">
          {job.status === 'running' && <Button variant="outline" onClick={() => cancel.mutate()} disabled={cancel.isPending}>Hủy</Button>}
          {(job.status === 'failed' || job.status === 'interrupted' || job.status === 'cancelled') &&
            <Button onClick={() => resume.mutate()} disabled={resume.isPending}>Chạy tiếp</Button>}
          {job.status === 'done' && job.slug && job.session_id &&
            <Button render={<Link to={`/p/${job.slug}/${job.session_id}`} />}>Mở dự án</Button>}
        </div>
      </div>

      <details className="rounded-xl border bg-card" open={job.status === 'running'}>
        <summary className="cursor-pointer px-5 py-3 text-sm font-medium">Nhật ký chi tiết</summary>
        <div className="px-5 pb-5">
          <label className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <input type="checkbox" checked={follow} onChange={(e) => setFollow(e.target.checked)} /> Tự cuộn xuống dòng mới
          </label>
          <pre ref={logRef} className="max-h-[420px] overflow-auto rounded-lg bg-neutral-950 p-3 text-xs leading-relaxed whitespace-pre-wrap text-neutral-200">
            {(log.length ? log : job.log).join('\n') || '…'}
          </pre>
        </div>
      </details>
    </main>
  )
}
