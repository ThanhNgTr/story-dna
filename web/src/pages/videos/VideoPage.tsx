import { useMutation, useQuery } from '@tanstack/react-query'
import { Languages, Palette, Play, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { Markdown } from '@/components/Markdown'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk, type AnalysisDetail } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { STEP_LABEL, fmtEta } from '@/lib/format'
import { cn } from '@/lib/utils'

const TABS = [['overview', 'Tổng quan'], ['story', 'Cốt truyện (EN)'], ['dna', 'DNA (EN)'], ['analysis', 'Phân tích chuyên sâu (EN)'], ['units', 'Các đoạn']] as const
const STYLE_LABEL: Record<string, string> = { story: 'Cách kể', pacing: 'Nhịp', camera: 'Máy quay', sound: 'Âm thanh', color: 'Màu & ánh sáng' }
const TIER: Record<string, string> = { main: 'chính', supporting: 'phụ', minor: 'thoáng qua' }

function CreateStyle({ a }: { a: AnalysisDetail }) {
  const navigate = useNavigate()
  const [slug, setSlug] = useState(a.suggested_slug)
  const [update, setUpdate] = useState(false)
  const skills = useQuery({ queryKey: qk.skills, queryFn: api.skills })
  const exists = skills.data?.some((s) => s.slug === slug)
  const create = useMutation({
    mutationFn: () => api.createSkill({ run_id: a.id, slug, update }),
    onSuccess: (job) => { askNotificationPermission(); toast.success('Claude đang tạo phong cách (khoảng 10–20 phút).'); navigate(`/jobs/${job.id}`) },
    onError: (e) => toast.error((e as Error).message),
  })
  return (
    <Dialog>
      <DialogTrigger render={<Button className="gap-1.5" disabled={!a.done || !!a.job} />}><Palette className="size-4" /> Tạo phong cách viết</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Tạo phong cách viết từ video này</DialogTitle>
          <DialogDescription>Claude biến cách kể của video thành một bộ luật viết series (cấu trúc mùa, nhịp, máy quay, âm thanh, màu). Nội dung truyện mẫu không bị chép sang series mới.</DialogDescription>
        </DialogHeader>
        <label className="text-sm font-medium">Tên phong cách
          <Input value={slug} onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))} className="mt-1 font-mono" />
        </label>
        <p className="text-xs text-muted-foreground">Chữ thường, không dấu, nối bằng gạch ngang. Dùng để gọi lệnh /write-series-{slug || '…'}.</p>
        {exists && (
          <label className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/5 p-3 text-sm">
            <input type="checkbox" checked={update} onChange={(e) => setUpdate(e.target.checked)} className="mt-0.5" />
            <span>Phong cách <b>{slug}</b> đã có. Tick để <b>cập nhật</b> nó bằng video này (thành phiên bản mới), hoặc đổi tên để tạo phong cách khác.</span>
          </label>
        )}
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Để sau</DialogClose>
          <Button disabled={!slug || (exists && !update) || create.isPending} onClick={() => create.mutate()}>{update ? 'Cập nhật phong cách' : 'Tạo phong cách'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Overview({ a }: { a: AnalysisDetail }) {
  const vi = a.summary_vi
  const summarize = useMutation({
    mutationFn: () => api.summarize('run', a.id),
    onSuccess: () => toast.success('Claude đang viết tóm tắt tiếng Việt (1–3 phút).'),
    onError: (e) => toast.error((e as Error).message),
  })
  if (!vi) {
    return (
      <div className="rounded-xl border bg-card p-6">
        {a.logline && <p className="text-muted-foreground">{a.logline}</p>}
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-lg bg-muted/50 p-4 text-sm">
          <Languages className="size-5 text-muted-foreground" />
          <span className="flex-1">Kết quả phân tích viết bằng tiếng Anh. Tạo bản tóm tắt tiếng Việt: cốt truyện, nhân vật, vì sao cuốn, phong cách.</span>
          <Button size="sm" disabled={!a.done || summarize.isPending} onClick={() => summarize.mutate()}>Tạo tóm tắt tiếng Việt</Button>
        </div>
      </div>
    )
  }
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-4">
        <section className="rounded-xl border bg-card p-6">
          {vi.logline_vi && <p className="text-lg leading-relaxed font-medium">{vi.logline_vi}</p>}
          {vi.synopsis_vi && <p className="mt-3 leading-relaxed text-muted-foreground">{vi.synopsis_vi}</p>}
          {vi.episodes_hint_vi && <p className="mt-3 text-sm"><b className="font-medium">Chia tập:</b> {vi.episodes_hint_vi}</p>}
        </section>
        {vi.why_it_hooks_vi?.length ? (
          <section className="rounded-xl border bg-card p-6">
            <h3 className="font-semibold">Vì sao người xem bị cuốn</h3>
            <ul className="mt-3 space-y-2">{vi.why_it_hooks_vi.map((x, i) => (
              <li key={i} className="flex gap-3 text-sm"><span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs text-primary">{i + 1}</span>{x}</li>
            ))}</ul>
          </section>
        ) : null}
        {vi.style_vi && (
          <section className="rounded-xl border bg-card p-6">
            <h3 className="font-semibold">Cách làm phim</h3>
            <dl className="mt-3 space-y-2 text-sm">
              {Object.entries(vi.style_vi).map(([k, v]) => (
                <div key={k} className="grid grid-cols-[120px_minmax(0,1fr)] gap-2"><dt className="text-muted-foreground">{STYLE_LABEL[k] ?? k}</dt><dd>{v}</dd></div>
              ))}
            </dl>
          </section>
        )}
      </div>
      <aside className="space-y-4">
        {vi.characters?.length ? (
          <section className="rounded-xl border bg-card p-5">
            <h3 className="font-semibold">Nhân vật</h3>
            <ul className="mt-3 space-y-3">
              {vi.characters.map((c) => (
                <li key={c.name} className="text-sm">
                  <div className="flex items-center gap-2"><span className="font-medium">{c.name}</span>
                    {c.tier && <StatusBadge tone={c.tier === 'main' ? 'run' : 'muted'}>{TIER[c.tier] ?? c.tier}</StatusBadge>}</div>
                  {c.role_vi && <div className="text-xs text-muted-foreground">{c.role_vi}</div>}
                  {c.desc_vi && <p className="mt-0.5 text-muted-foreground">{c.desc_vi}</p>}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
        <button className="text-xs text-muted-foreground hover:text-foreground" disabled={summarize.isPending} onClick={() => summarize.mutate()}>Viết lại tóm tắt tiếng Việt</button>
      </aside>
    </div>
  )
}

function Doc({ id, kind }: { id: string; kind: string }) {
  const { data, isLoading, error } = useQuery({ queryKey: ['analysis-doc', id, kind], queryFn: () => api.analysisDoc(id, kind) })
  if (isLoading) return <Skeleton className="h-96" />
  if (error) return <p className="text-sm text-muted-foreground">{(error as Error).message}</p>
  return <div className="rounded-xl border bg-card p-6"><Markdown>{data!.markdown}</Markdown></div>
}

function Units({ a }: { a: AnalysisDetail }) {
  const done = a.units.filter((u) => u.done).length
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="flex items-center gap-3 text-sm"><span>{done}/{a.units.length} đoạn đã phân tích</span><Progress value={(100 * done) / Math.max(1, a.units.length)} className="h-1.5 max-w-xs flex-1" /></div>
      <p className="mt-1 text-xs text-muted-foreground">Video được cắt thành các đoạn ~2 phút đúng chỗ chuyển cảnh; mỗi đoạn một Claude xem.</p>
      <div className="mt-4 grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-2">
        {a.units.map((u) => (
          <div key={u.id} className={cn('rounded-md border px-2.5 py-2 text-xs', u.done ? 'border-success/30 bg-success/5' : 'bg-muted/40')}>
            <div className="font-mono">{u.id}</div>
            <div className="text-muted-foreground">{(u.start / 60).toFixed(1)}–{(u.end / 60).toFixed(1)} phút</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function VideoPage() {
  const { id = '' } = useParams()
  const [tab, setTab] = useState<(typeof TABS)[number][0]>('overview')
  const { data: a, isLoading, error } = useQuery({ queryKey: qk.analysis(id), queryFn: () => api.analysis(id) })
  const resume = useMutation({
    mutationFn: () => api.resumeAnalysis(id),
    onSuccess: () => toast.success('Đã chạy tiếp. Các đoạn đã xong được bỏ qua.'),
    onError: (e) => toast.error((e as Error).message),
  })
  if (error) return <main className="mx-auto max-w-5xl p-10 text-destructive">{(error as Error).message}</main>
  if (isLoading || !a) return <main className="mx-auto max-w-5xl space-y-4 p-10"><Skeleton className="h-24" /><Skeleton className="h-96" /></main>
  const runningStep = a.job && Object.entries(a.job.steps).find(([, s]) => s.status === 'running')?.[0]
  const title = a.summary_vi?.title_vi || a.title || a.sources.map((s) => s.filename).join(', ')
  return (
    <main className="mx-auto max-w-6xl space-y-5 px-4 py-8">
      <div>
        <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">← Dự án</Link>
        <div className="mt-1 flex flex-wrap items-start gap-3">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {a.summary_vi?.genre_vi || a.genre}{a.minutes ? ` · ${a.minutes} phút` : ''}{a.language ? ` · thoại ${a.language}` : ''} · {a.sources.map((s) => s.filename).join(', ')}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {a.job ? <StatusBadge tone="run">Đang phân tích</StatusBadge> : a.done ? <StatusBadge tone="ok">Đã học xong</StatusBadge> : <StatusBadge tone="warn">Chưa xong</StatusBadge>}
              {a.skills.map((s) => <Link key={s} to={`/styles/${s}`}><StatusBadge tone="muted"><Palette className="size-3" />{s}</StatusBadge></Link>)}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {!a.done && !a.job && <Button variant="outline" className="gap-1.5" onClick={() => resume.mutate()} disabled={resume.isPending}><Play className="size-4" />Chạy tiếp</Button>}
            <CreateStyle a={a} />
          </div>
        </div>
      </div>
      {a.job && (
        <Link to={`/jobs/${a.job.id}`} className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-2.5 text-sm hover:bg-primary/10">
          <span className="size-2 animate-pulse rounded-full bg-primary" /><span className="font-medium">{a.job.title}</span>
          {runningStep && <span className="text-muted-foreground">· {STEP_LABEL[runningStep] ?? runningStep}</span>}
          <span className="ml-auto text-primary">{fmtEta(a.job.eta_sec) ? `${fmtEta(a.job.eta_sec)} · ` : ''}Xem tiến độ →</span>
        </Link>
      )}
      {a.skills.length > 0 && a.done && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card px-4 py-3 text-sm">
          <Sparkles className="size-4 text-primary" /> Đã có phong cách từ video này.
          <Button size="sm" render={<Link to={`/new?skill=${a.skills[0]}`} />} className="ml-auto">Viết series với {a.skills[0]}</Button>
        </div>
      )}
      <nav className="flex flex-wrap gap-1 border-b">
        {TABS.filter(([k]) => k === 'overview' || k === 'units' || a.docs[k as 'story' | 'dna' | 'analysis']).map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            className={cn('-mb-px border-b-2 px-3 py-2 text-sm', tab === k ? 'border-primary font-medium' : 'border-transparent text-muted-foreground hover:text-foreground')}>{label}</button>
        ))}
      </nav>
      {tab === 'overview' && <Overview a={a} />}
      {(tab === 'story' || tab === 'dna' || tab === 'analysis') && <Doc id={a.id} kind={tab} />}
      {tab === 'units' && <Units a={a} />}
    </main>
  )
}
