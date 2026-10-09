import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, PenLine, RefreshCw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk, type EditorDim, type EditorFinding, type EditorReview } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { fmtDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

export const DIM_LABEL: Record<EditorDim, string> = {
  theme: 'Chủ đề',
  protagonist: 'Chiều sâu nhân vật chính',
  supporting_cast: 'Nhân vật phụ',
  antagonist: 'Phản diện / lực cản',
  dialogue: 'Lời thoại và ẩn ý',
  setup_payoff: 'Gài và trả, cú lật công bằng',
  stakes: 'Mức cược và leo thang',
  emotion: 'Cảm xúc, cảnh có bước ngoặt',
  originality: 'Độc đáo, tránh sáo mòn',
}
const DIMS = Object.keys(DIM_LABEL) as EditorDim[]
const SEV: Record<EditorFinding['severity'], { label: string; cls: string }> = {
  high: { label: 'Nặng', cls: 'bg-destructive/10 text-destructive' },
  medium: { label: 'Vừa', cls: 'bg-warning/10 text-warning' },
  low: { label: 'Nhẹ', cls: 'bg-muted text-muted-foreground' },
}

function scoreTone(s: number) {
  return s >= 4 ? 'bg-success' : s >= 3 ? 'bg-warning' : 'bg-destructive'
}

function RunReview({ label, variant = 'default' }: { label: string; variant?: 'default' | 'outline' }) {
  const p = useProject()
  const qc = useQueryClient()
  const run = useMutation({
    mutationFn: () => api.runEditor(p.slug, p.session_id, { mode: 'review' }),
    onSuccess: () => {
      askNotificationPermission()
      toast.success('Claude đang biên tập (khoảng 5–15 phút). Xong sẽ có thông báo.')
      qc.invalidateQueries({ queryKey: qk.project(p.slug, p.session_id) })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  return (
    <ConfirmAction trigger={<Button variant={variant} size="sm" className="gap-1.5" disabled={!!p.job}><RefreshCw className="size-3.5" /> {label}</Button>}
      title="Biên tập kịch bản?" confirmLabel="Biên tập" pending={run.isPending} onConfirm={() => run.mutateAsync()}
      description="Claude đọc bible, outline và các tập như một biên tập viên: chấm 9 tiêu chí chiều sâu, chỉ ra chỗ yếu kèm dẫn chứng và cách sửa. Chưa sửa gì vào kịch bản." />
  )
}

function Where({ f }: { f: EditorFinding }) {
  const p = useProject()
  const base = `/p/${p.slug}/${p.session_id}`
  const w = f.where
  const text = [w.episode ? `Tập ${w.episode}` : null, w.scene, w.field, !w.episode ? w.file : null].filter(Boolean).join(' · ')
  if (w.episode) return <Link to={`${base}/ep/${w.episode}`} className="text-primary hover:underline">{text}</Link>
  const kind = /bible/.test(w.file) ? 'bible' : /outline/.test(w.file) ? 'outline' : null
  return kind ? <Link to={`${base}/doc/${kind}`} className="text-primary hover:underline">{text}</Link> : <span>{text}</span>
}

function FindingCard({ f, checked, applied, onToggle }: {
  f: EditorFinding; checked: boolean; applied: boolean; onToggle: () => void
}) {
  return (
    <li className={cn('rounded-lg border p-4', applied && 'opacity-60')}>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <input type="checkbox" className="size-4 accent-primary" checked={checked} disabled={applied} onChange={onToggle}
          aria-label={`Chọn ${f.id}`} />
        <span className="font-mono font-medium">{f.id}</span>
        <span className={cn('rounded px-1.5 py-0.5 font-medium', SEV[f.severity].cls)}>{SEV[f.severity].label}</span>
        <span className="text-muted-foreground">{DIM_LABEL[f.dimension] ?? f.dimension}</span>
        <span className="text-muted-foreground">·</span>
        <Where f={f} />
        {applied && <span className="ml-auto flex items-center gap-1 text-success"><CheckCircle2 className="size-3.5" /> Đã sửa</span>}
      </div>
      <blockquote className="mt-3 border-l-2 pl-3 font-serif text-sm italic text-muted-foreground">{f.evidence}</blockquote>
      <p className="mt-2 text-sm"><span className="font-medium">Vấn đề: </span>{f.problem}</p>
      <p className="mt-1.5 text-sm"><span className="font-medium text-primary">Cách sửa: </span>{f.fix}</p>
      {f.affects?.length ? <p className="mt-2 text-xs text-muted-foreground">Sẽ viết lại: {f.affects.join(', ')}</p> : null}
    </li>
  )
}

function Review({ r }: { r: EditorReview }) {
  const p = useProject()
  const qc = useQueryClient()
  const [sel, setSel] = useState<Set<string>>(new Set())
  const [rereview, setRereview] = useState(true)
  useEffect(() => {
    setSel(new Set(r.findings.filter((f) => f.severity !== 'low' && !r.applied.includes(f.id)).map((f) => f.id)))
  }, [r])
  const groups = useMemo(() => (['high', 'medium', 'low'] as const)
    .map((s) => [s, r.findings.filter((f) => f.severity === s)] as const).filter(([, fs]) => fs.length), [r])
  const apply = useMutation({
    mutationFn: () => api.runEditor(p.slug, p.session_id, { mode: 'apply', ids: [...sel], rereview }),
    onSuccess: () => {
      askNotificationPermission()
      toast.success(`Claude đang sửa ${sel.size} điểm. Bản cũ được giữ, xong sẽ có thông báo.`)
      qc.invalidateQueries({ queryKey: qk.project(p.slug, p.session_id) })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })

  return (
    <div className="space-y-6">
      <div className="rounded-xl border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold"><PenLine className="size-5" /> Biên tập kịch bản</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Bản {r.file.replace('.json', '')} · {r.stage === 'outline' ? 'chấm trên bible + outline' : 'chấm trên các tập đã viết'} · {fmtDate(r.created_at)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={cn('rounded-lg px-3 py-1.5 text-center', r.verdict === 'pass' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning')}>
              <div className="text-2xl font-semibold tabular-nums">{r.average.toFixed(1)}<span className="text-sm">/5</span></div>
              <div className="text-xs font-medium">{r.verdict === 'pass' ? 'Đạt' : 'Cần sửa'}</div>
            </div>
            <RunReview label="Biên tập lại" variant="outline" />
          </div>
        </div>
        {r.stale && (
          <p className="mt-4 flex items-center gap-2 rounded-md bg-warning/10 px-3 py-2 text-sm text-warning">
            <AlertTriangle className="size-4 shrink-0" /> Kịch bản đã có bản mới hơn lần biên tập này. Bấm “Biên tập lại” để chấm bản mới.
          </p>
        )}
        <p className="mt-4 text-sm leading-relaxed">{r.summary}</p>
        <p className="mt-3 text-sm"><span className="font-medium">Câu hỏi chủ đề: </span><span className="italic">{r.theme_statement}</span></p>
      </div>

      <section className="rounded-xl border bg-card p-6">
        <h2 className="font-semibold">Điểm theo tiêu chí</h2>
        <p className="mt-1 text-xs text-muted-foreground">Đạt khi mọi tiêu chí từ 3 trở lên và trung bình từ 3.5. Bấm vào một dòng để xem lý do và dẫn chứng.</p>
        <ul className="mt-4 space-y-1">
          {DIMS.map((d) => {
            const s = r.scores[d]
            if (!s) return null
            return (
              <li key={d}>
                <details className="group rounded-md px-2 py-1.5 hover:bg-muted/50">
                  <summary className="flex cursor-pointer list-none items-center gap-3 text-sm">
                    <span className="w-56 shrink-0">{DIM_LABEL[d]}</span>
                    <span className="flex flex-1 gap-1">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <span key={i} className={cn('h-2 flex-1 rounded-full', i <= s.score ? scoreTone(s.score) : 'bg-muted')} />
                      ))}
                    </span>
                    <span className="w-8 text-right font-medium tabular-nums">{s.score}</span>
                  </summary>
                  <div className="mt-2 ml-1 space-y-1.5 text-sm text-muted-foreground">
                    <p>{s.why}</p>
                    {s.evidence?.map((e, i) => <p key={i} className="border-l-2 pl-3 font-serif italic">{e}</p>)}
                  </div>
                </details>
              </li>
            )
          })}
        </ul>
      </section>

      <section className="rounded-xl border bg-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold">Điểm cần sửa ({r.findings.length})</h2>
            <p className="mt-1 text-xs text-muted-foreground">Mặc định chọn các điểm Nặng và Vừa. Claude viết phiên bản mới cho bible / outline / các tập liên quan; bản cũ được giữ để so sánh.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <input type="checkbox" className="accent-primary" checked={rereview} onChange={(e) => setRereview(e.target.checked)} />
              Biên tập lại sau khi sửa
            </label>
            <ConfirmAction trigger={<Button size="sm" disabled={!sel.size || !!p.job}>Áp dụng {sel.size} sửa đã chọn</Button>}
              title={`Áp dụng ${sel.size} sửa?`} confirmLabel="Áp dụng" pending={apply.isPending} onConfirm={() => apply.mutateAsync()}
              description={<>Claude sửa {[...sel].join(', ')} (khoảng {Math.max(5, sel.size * 3)}–{Math.max(10, sel.size * 6)} phút), sau đó tự kiểm tra cốt truyện{rereview ? ' và biên tập lại' : ''}. Tập đã quay (canon) không bị viết lại.</>} />
          </div>
        </div>
        {groups.map(([s, fs]) => (
          <div key={s} className="mt-5">
            <h3 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">{SEV[s].label} ({fs.length})</h3>
            <ul className="space-y-3">
              {fs.map((f) => <FindingCard key={f.id} f={f} checked={sel.has(f.id)} applied={r.applied.includes(f.id)} onToggle={() => toggle(f.id)} />)}
            </ul>
          </div>
        ))}
      </section>

      {r.setup_payoff_map?.length ? (
        <section className="rounded-xl border bg-card p-6">
          <h2 className="font-semibold">Gài và trả</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted-foreground">
                <tr><th className="py-1.5 pr-3">Chi tiết gài</th><th className="pr-3">Tập</th><th className="pr-3">Được trả bằng</th><th>Tập</th></tr>
              </thead>
              <tbody>
                {r.setup_payoff_map.map((x, i) => (
                  <tr key={i} className="border-t align-top">
                    <td className="py-1.5 pr-3">{x.plant}</td>
                    <td className="pr-3 tabular-nums">{x.plant_ep ?? '-'}</td>
                    <td className={cn('pr-3', !x.payoff && 'text-destructive')}>{x.payoff ?? 'Chưa được trả'}</td>
                    <td className="tabular-nums">{x.payoff_ep ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {r.strengths?.length ? (
        <section className="rounded-xl border bg-card p-6">
          <h2 className="font-semibold">Điểm mạnh nên giữ</h2>
          <ul className="mt-3 space-y-1.5 text-sm">
            {r.strengths.map((s, i) => <li key={i} className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />{s}</li>)}
          </ul>
        </section>
      ) : null}
    </div>
  )
}

export function EditorPage() {
  const p = useProject()
  const { data, isLoading } = useQuery({
    queryKey: qk.editor(p.slug, p.session_id),
    queryFn: () => api.editor(p.slug, p.session_id),
    enabled: !!p.editor,
    retry: false,
  })
  if (!p.editor) {
    return (
      <div className="rounded-xl border bg-card p-6">
        <h1 className="flex items-center gap-2 text-xl font-semibold"><PenLine className="size-5" /> Biên tập kịch bản</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Kiểm tra cốt truyện chỉ xem kịch bản có đủ phần hay không. Biên tập xem các phần đó có hay không: chủ đề, chiều sâu nhân vật chính,
          nhân vật phụ, động cơ phản diện, ẩn ý trong thoại, gài và trả, mức cược, cảm xúc, độ độc đáo. Mỗi điểm chấm đều có dẫn chứng
          (tập, cảnh, câu thoại) và cách sửa cụ thể; bạn chọn điểm nào thì Claude sửa điểm đó.
        </p>
        <div className="mt-4">{p.job ? <p className="text-sm text-muted-foreground">Đang có việc chạy cho series này.</p> : <RunReview label="Biên tập ngay" />}</div>
      </div>
    )
  }
  if (isLoading || !data) return <Skeleton className="h-96" />
  return <Review r={data} />
}
