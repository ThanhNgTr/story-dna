import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, CheckCircle2, GitBranch, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { api, qk, type LogicFinding, type LogicKind, type Project } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'
import { SEV, Where } from './EditorPage'

/** [C0]..[C8] of story-continuity/references/continuity.md, in display order. */
const CHECKS: [number, string][] = [
  [1, 'Chuỗi nhân quả: tập nào cũng xảy ra vì một sự kiện trước đó'],
  [6, 'Nối tập: mỗi tập mở tiếp đúng cliffhanger của tập trước'],
  [2, 'Ai biết gì: không nhân vật nào dùng điều mình chưa biết'],
  [7, 'Manh mối và chi tiết gài có trên màn hình, được trả'],
  [3, 'Trạng thái nhân vật: đã chết / đã đi thì không tự xuất hiện'],
  [4, 'Đồ vật: mất / hỏng thì không tự quay lại'],
  [5, 'Thời gian: ngày không chạy lùi, khớp bible'],
  [8, 'Quan hệ đổi có lý do trên màn hình'],
  [0, 'Sổ trạng thái (ai biết gì, ở đâu, cầm gì sau từng tập)'],
]

const KIND: Record<LogicKind, string> = {
  contradiction: 'Mâu thuẫn',
  knowledge: 'Biết trước khi được biết',
  motive: 'Động cơ khó tin',
  coincidence: 'Trùng hợp',
  easier_path: 'Có cách dễ hơn',
  timeline: 'Thời gian không khớp',
  cause_missing: 'Thiếu nguyên nhân',
  dropped_thread: 'Bỏ lửng',
  world_rule: 'Phá luật thế giới',
}

function LogicFindings({ p }: { p: Project }) {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: qk.continuity(p.slug, p.session_id), queryFn: () => api.continuity(p.slug, p.session_id) })
  const logic = q.data?.logic
  const [sel, setSel] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (logic) setSel(new Set(logic.findings.filter((f) => f.severity !== 'low' && !logic.applied.includes(f.id)).map((f) => f.id)))
  }, [logic])
  const sorted = useMemo(() => {
    const order = { high: 0, medium: 1, low: 2 }
    return [...(logic?.findings ?? [])].sort((a, b) => order[a.severity] - order[b.severity])
  }, [logic])
  const apply = useMutation({
    mutationFn: () => api.runContinuity(p.slug, p.session_id, { mode: 'apply', ids: [...sel] }),
    onSuccess: () => {
      askNotificationPermission()
      toast.success(`Claude đang sửa ${sel.size} lỗi logic. Bản cũ được giữ, xong sẽ có thông báo.`)
      qc.invalidateQueries({ queryKey: qk.project(p.slug, p.session_id) })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  if (q.isLoading) return <p className="mt-2 text-xs text-muted-foreground">Đang tải…</p>
  if (!logic) return null
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  return (
    <div className="mt-3 space-y-3">
      <p className="text-muted-foreground">{logic.summary}</p>
      {sorted.length ? (
        <ul className="space-y-2">
          {sorted.map((f: LogicFinding) => {
            const applied = logic.applied.includes(f.id)
            return (
              <li key={f.id} className={cn('rounded-lg border p-3', applied && 'opacity-60')}>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <input type="checkbox" className="size-4 accent-primary" checked={sel.has(f.id)} disabled={applied}
                    onChange={() => toggle(f.id)} aria-label={`Chọn ${f.id}`} />
                  <span className="font-mono font-medium">{f.id}</span>
                  <span className={cn('rounded px-1.5 py-0.5 font-medium', SEV[f.severity].cls)}>{SEV[f.severity].label}</span>
                  <span className="text-muted-foreground">{KIND[f.kind] ?? f.kind}</span>
                  <span className="text-muted-foreground">·</span>
                  <Where f={f} />
                  {applied && <span className="ml-auto flex items-center gap-1 text-success"><CheckCircle2 className="size-3.5" /> Đã sửa</span>}
                </div>
                <blockquote className="mt-2 border-l-2 pl-3 font-serif text-sm italic text-muted-foreground">{f.evidence}</blockquote>
                <p className="mt-1.5"><span className="font-medium">Vấn đề: </span>{f.problem}</p>
                <p className="mt-1"><span className="font-medium text-primary">Cách sửa: </span>{f.fix}</p>
              </li>
            )
          })}
        </ul>
      ) : <p className="text-success">Không tìm thấy lỗ hổng logic.</p>}
      {sel.size > 0 && !p.job && (
        <ConfirmAction trigger={<Button size="sm">Sửa {sel.size} lỗi logic đã chọn</Button>} title="Sửa lỗi logic?"
          description={<>Claude viết phiên bản mới cho các tập / bible / outline liên quan, rồi kiểm tra lại cốt truyện và liên mạch. Bản cũ được giữ.</>}
          confirmLabel="Sửa" pending={apply.isPending} onConfirm={() => apply.mutateAsync()} />
      )}
    </div>
  )
}

export function ContinuityCard({ p }: { p: Project }) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const run = useMutation({
    mutationFn: (mode: 'fix' | 'review') => api.runContinuity(p.slug, p.session_id, { mode }),
    onSuccess: (_, mode) => {
      askNotificationPermission()
      toast.success(mode === 'fix' ? 'Claude đang sửa liên mạch. Xong sẽ có thông báo.'
        : 'Claude đang rà logic toàn mùa (khoảng 5–15 phút). Xong sẽ có thông báo.')
      qc.invalidateQueries({ queryKey: qk.project(p.slug, p.session_id) })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const c = p.continuity
  if (!c) return null
  const byCode = new Map(CHECKS.map(([code]) => [code, c.errors.filter((e) => e.startsWith(`[C${code}]`))]))
  const rows = CHECKS.filter(([code]) => c.stage === 'episodes' || code === 1)
  const lg = c.logic
  return (
    <section className="rounded-xl border bg-card p-5 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <GitBranch className="size-4" /> Liên mạch giữa các tập
          <span className="font-normal text-muted-foreground">({c.stage === 'outline' ? 'outline' : 'outline + các tập'})</span>
        </div>
        {!p.job && (
          <div className="flex flex-wrap gap-2">
            {!c.ok && (
              <ConfirmAction trigger={<Button size="sm">Sửa tự động</Button>} title="Sửa liên mạch?"
                description={<>Claude sửa {c.errors.length} lỗi: lập sổ trạng thái nếu chưa có, viết phiên bản mới cho outline / các tập bị đứt mạch. Bản cũ được giữ.</>}
                confirmLabel="Sửa" pending={run.isPending} onConfirm={() => run.mutateAsync('fix')} />
            )}
            <ConfirmAction trigger={<Button size="sm" variant="outline">{lg ? 'Rà logic lại' : 'Rà logic'}</Button>} title="Rà logic toàn mùa?"
              description="Claude đọc cả mùa theo thứ tự như khán giả: tìm mâu thuẫn, trùng hợp, động cơ khó tin, cách giải quyết dễ hơn bị bỏ qua, chi tiết bỏ lửng. Chưa sửa gì vào kịch bản."
              confirmLabel="Rà" pending={run.isPending} onConfirm={() => run.mutateAsync('review')} />
          </div>
        )}
      </div>
      <ul className="mt-3 space-y-1.5">
        {rows.map(([code, label]) => {
          const errs = byCode.get(code) ?? []
          return (
            <li key={code}>
              <details className="group">
                <summary className={cn('flex cursor-pointer list-none items-center gap-2', !errs.length && 'cursor-default')}>
                  {errs.length ? <X className="size-4 shrink-0 text-destructive" /> : <Check className="size-4 shrink-0 text-success" />}
                  <span>{label}</span>
                  {errs.length > 0 && <span className="text-xs text-muted-foreground">{errs.length} lỗi</span>}
                </summary>
                {errs.length > 0 && (
                  <ul className="mt-1 ml-6 list-disc space-y-0.5 pl-4 text-xs text-muted-foreground">
                    {errs.map((e) => <li key={e}>{e.replace(/^\[C\d\] /, '')}</li>)}
                  </ul>
                )}
              </details>
            </li>
          )
        })}
      </ul>
      {lg && (
        <div className="mt-4 border-t pt-3">
          <button type="button" onClick={() => setOpen((o) => !o)} className="flex w-full flex-wrap items-center gap-3 text-left">
            <span className="font-medium">Rà logic</span>
            <span className={cn('font-semibold', lg.verdict === 'pass' ? 'text-success' : 'text-warning')}>
              {lg.verdict === 'pass' ? 'Đạt' : 'Cần sửa'}
            </span>
            <span className="text-muted-foreground">
              {lg.findings.high} nặng, {lg.findings.medium} vừa, {lg.findings.low} nhẹ
              {lg.applied ? ` · đã sửa ${lg.applied}` : ''}{lg.stale ? ' · kịch bản đã đổi, nên rà lại' : ''}
            </span>
            <span className="ml-auto text-primary">{open ? 'Ẩn' : 'Xem'}</span>
          </button>
          {open && <LogicFindings p={p} />}
        </div>
      )}
    </section>
  )
}
