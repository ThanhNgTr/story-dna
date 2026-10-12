import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Clapperboard, EyeOff, Film, MoreHorizontal, Palette, Plus, Search, Undo2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { JobRow } from '@/components/JobCenter'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { api, legacy, qk, type Analysis, type ProjectSummary, type Skill } from '@/lib/api'
import { fmtDate } from '@/lib/format'
import { cn } from '@/lib/utils'

type Filter = 'all' | 'active' | 'review' | 'final'
const FILTERS: [Filter, string][] = [['all', 'Tất cả'], ['review', 'Chờ bạn duyệt'], ['active', 'Đang làm'], ['final', 'Đã chốt']]

function matches(p: ProjectSummary, f: Filter): boolean {
  if (f === 'all') return true
  if (f === 'final') return p.final
  if (f === 'review') return !p.final && p.stage.tone === 'warn'
  return !p.final
}

function useHide() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ kind, item }: { kind: 'runs' | 'series' | 'skills'; item: string }) => api.hide(kind, item),
    onSuccess: () => {
      for (const k of [qk.projects, qk.skills, qk.analyses, qk.hidden]) qc.invalidateQueries({ queryKey: k })
      toast.success('Đã ẩn. Khôi phục được ở "Mục đã ẩn" cuối trang.')
    },
    onError: (e) => toast.error((e as Error).message),
  })
}

function ProjectCard({ p, onHide }: { p: ProjectSummary; onHide: () => void }) {
  const planned = p.planned || p.episodes || 1
  const pct = Math.min(100, Math.round((100 * (p.episodes + p.produced)) / planned))
  return (
    <div className="group relative flex flex-col rounded-xl border bg-card shadow-xs transition hover:border-primary/40 hover:shadow-md">
      <Link to={`/p/${p.slug}/${p.session_id}`} className="flex flex-1 flex-col p-5">
        <div className="flex items-start justify-between gap-3 pr-7">
          <div className="min-w-0">
            <h3 className="truncate text-lg font-semibold">{p.title}</h3>
            <p className="mt-0.5 text-sm text-muted-foreground">Phong cách {p.slug}</p>
          </div>
        </div>
        <div className="mt-3"><StatusBadge tone={p.stage.tone}>{p.stage.label}</StatusBadge></div>
        <div className="mt-5">
          <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
            <span>{p.episodes} / {planned} tập{p.episode_sec ? ` × ${p.episode_sec}s` : ''}{p.produced ? ` · ${p.produced} đã quay` : ''}</span>
            <span>{pct}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div className={cn('h-full rounded-full transition-all', p.final ? 'bg-success' : 'bg-primary')} style={{ width: `${pct}%` }} />
          </div>
        </div>
        <div className="mt-auto flex items-center justify-between pt-5 text-sm">
          <span className="text-xs text-muted-foreground">{fmtDate(p.created_at) || p.session_id}</span>
          <span className="flex items-center gap-1 font-medium text-primary">Mở <ArrowRight className="size-4 transition group-hover:translate-x-0.5" /></span>
        </div>
      </Link>
      <div className="absolute top-3 right-3">
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="icon-sm" aria-label="Thêm" />}><MoreHorizontal className="size-4" /></DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem render={<a href={`/series/${p.slug}/${p.session_id}/export`} />}>Tải file biên kịch .md</DropdownMenuItem>
            <DropdownMenuItem onClick={onHide}><EyeOff className="size-4" /> Ẩn dự án</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

function SkillCard({ s, onHide }: { s: Skill; onHide: () => Promise<unknown> }) {
  return (
    <div className="flex flex-col rounded-xl border bg-card p-5">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground"><Palette className="size-4" /></span>
        <div className="min-w-0">
          <div className="truncate font-semibold">{s.slug}</div>
          <div className="text-xs text-muted-foreground">{s.version}{s.projects ? ` · ${s.projects} series` : ''}</div>
        </div>
      </div>
      <p className="mt-3 line-clamp-4 text-sm text-muted-foreground">{s.tagline_vi || s.description || 'Chưa có mô tả.'}</p>
      {s.reference && (
        <p className="mt-2 text-xs text-muted-foreground">
          Học từ: {s.reference.title || s.reference.sources.join(', ')} ({s.reference.minutes} phút)
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button render={<Link to={`/new?skill=${s.slug}`} />} variant="outline" size="sm">Viết series</Button>
        <Button render={<Link to={`/styles/${s.slug}`} />} variant="ghost" size="sm">Xem luật</Button>
        <ConfirmAction
          trigger={<Button variant="ghost" size="sm" className="ml-auto gap-1 text-muted-foreground"><EyeOff className="size-3.5" />Ẩn</Button>}
          title={`Ẩn phong cách ${s.slug}?`}
          description={<>Phong cách được cất vào <code>data/archive/skills/</code>: không bị xóa, nhưng trong lúc ẩn Claude không dùng được nó
            (không viết series mới, không sửa{s.projects ? `, ${s.projects} series đang dùng phong cách này cũng không gửi góp ý được` : ''}).
            Khôi phục ở “Mục đã ẩn” cuối trang.</>}
          confirmLabel="Ẩn phong cách" onConfirm={onHide} />
      </div>
    </div>
  )
}

function AnalysisRow({ a, onHide }: { a: Analysis; onHide: () => void }) {
  const name = a.title_vi || a.title || a.genre_vi || a.genre || a.sources.join(', ')
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
      <Film className="size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{name}</div>
        <div className="truncate text-xs text-muted-foreground">
          {a.sources.join(', ')} · {a.minutes} phút{a.language ? ` · thoại ${a.language}` : ''}
          {a.skills.length > 0 && ` · phong cách: ${a.skills.join(', ')}`}
        </div>
      </div>
      {a.job ? <StatusBadge tone="run">Đang phân tích</StatusBadge>
        : a.done ? <StatusBadge tone="ok">Xong</StatusBadge>
          : <StatusBadge tone="warn">Chưa xong ({a.analyzed}/{a.units})</StatusBadge>}
      <Link to={`/videos/${a.id}`} className="text-sm text-primary hover:underline">Xem</Link>
      {!a.job && <button onClick={onHide} className="text-xs text-muted-foreground hover:text-foreground">Ẩn</button>}
    </div>
  )
}

function HiddenDialog() {
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: qk.hidden, queryFn: api.hidden })
  const restore = useMutation({
    mutationFn: ({ kind, item }: { kind: 'runs' | 'series' | 'jobs' | 'skills'; item: string }) => api.unhide(kind, item),
    onSuccess: () => { for (const k of [qk.projects, qk.skills, qk.analyses, qk.hidden]) qc.invalidateQueries({ queryKey: k }) },
    onError: (e) => toast.error((e as Error).message),
  })
  const groups: ['series' | 'skills' | 'runs', string][] = [['series', 'Dự án'], ['skills', 'Phong cách'], ['runs', 'Video mẫu']]
  const total = data ? groups.reduce((n, [k]) => n + data[k].length, 0) : 0
  if (!total) return null
  return (
    <Dialog>
      <DialogTrigger render={<button className="text-sm text-muted-foreground hover:text-foreground" />}>Mục đã ẩn ({total})</DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Mục đã ẩn</DialogTitle></DialogHeader>
        <p className="text-sm text-muted-foreground">Không có gì bị xóa. Khôi phục để thấy lại.</p>
        <div className="max-h-[50vh] space-y-4 overflow-y-auto">
          {groups.map(([k, label]) => data![k].length ? (
            <div key={k}>
              <div className="mb-1 text-xs font-medium text-muted-foreground uppercase">{label}</div>
              {data![k].map((item) => (
                <div key={item} className="flex items-center justify-between gap-2 py-1 text-sm">
                  <span className="truncate">{item}</span>
                  <Button size="xs" variant="outline" className="gap-1" onClick={() => restore.mutate({ kind: k, item })}><Undo2 className="size-3" />Khôi phục</Button>
                </div>
              ))}
            </div>
          ) : null)}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function HomePage() {
  const projects = useQuery({ queryKey: qk.projects, queryFn: api.projects })
  const skills = useQuery({ queryKey: qk.skills, queryFn: api.skills })
  const analyses = useQuery({ queryKey: qk.analyses, queryFn: api.analyses })
  const jobs = useQuery({ queryKey: qk.jobs, queryFn: () => api.jobs(15) })
  const hide = useHide()
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState<Filter>('all')
  const running = (jobs.data ?? []).filter((j) => j.status === 'running')
  const list = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (projects.data ?? [])
      .filter((p) => matches(p, filter))
      .filter((p) => !needle || `${p.title} ${p.slug}`.toLowerCase().includes(needle))
      .sort((a, b) => (b.created_at ?? b.session_id).localeCompare(a.created_at ?? a.session_id))
  }, [projects.data, q, filter])
  const noSkills = !!skills.data && !skills.data.length

  return (
    <main className="mx-auto max-w-6xl space-y-12 px-4 py-10">
      <section>
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Dự án của bạn</h1>
            <p className="mt-1 text-muted-foreground">Mỗi dự án là một series: ý tưởng, bible, outline, kịch bản và ngoại hình.</p>
          </div>
          <div className="flex gap-2">
            <Button render={<Link to="/continue" />} variant="outline" disabled={!!noSkills}>Viết tiếp từ video đã quay</Button>
            <Button render={<Link to="/new" />} className="gap-1.5" disabled={!!noSkills}><Plus className="size-4" /> Series mới</Button>
          </div>
        </div>

        {running.length > 0 && (
          <div className="mb-6 rounded-xl border border-primary/30 bg-primary/5 p-4">
            <div className="mb-3 text-sm font-medium">Đang chạy</div>
            <div className="grid gap-2 md:grid-cols-2">{running.map((j) => <JobRow key={j.id} job={j} />)}</div>
          </div>
        )}

        {(projects.data?.length ?? 0) > 0 && (
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-2 left-2.5 size-4 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm dự án" className="pl-8" />
            </div>
            <div className="flex flex-wrap gap-1">
              {FILTERS.map(([f, label]) => (
                <button key={f} onClick={() => setFilter(f)}
                  className={cn('rounded-full border px-3 py-1 text-sm', filter === f ? 'border-primary/40 bg-accent font-medium text-accent-foreground' : 'text-muted-foreground hover:text-foreground')}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {projects.error ? (
          <p className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">Chưa tải được danh sách dự án.</p>
        ) : projects.isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-48 rounded-xl" />)}</div>
        ) : list.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((p) => <ProjectCard key={p.slug + p.session_id} p={p} onHide={() => hide.mutate({ kind: 'series', item: `${p.slug}/${p.session_id}` })} />)}
          </div>
        ) : projects.data?.length ? (
          <p className="text-sm text-muted-foreground">Không có dự án nào khớp.</p>
        ) : (
          <div className="flex flex-col items-center rounded-xl border border-dashed px-6 py-14 text-center">
            <Clapperboard className="size-10 text-muted-foreground" />
            <h2 className="mt-4 text-lg font-medium">Chưa có dự án nào</h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {noSkills ? 'Bắt đầu bằng việc học một video mẫu: Claude rút ra cách kể chuyện, rồi bạn viết series theo phong cách đó.'
                : 'Chọn một phong cách bên dưới và đưa ý tưởng của bạn vào để viết series 10–20 tập.'}
            </p>
            <div className="mt-6 flex gap-2">
              <Button render={<Link to="/videos/new" />} variant={noSkills ? 'default' : 'outline'}>Học video mẫu</Button>
              {!noSkills && <Button render={<Link to="/new" />}>Viết series mới</Button>}
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Phong cách viết</h2>
            <p className="text-sm text-muted-foreground">Mỗi phong cách được học từ một video mẫu: cấu trúc truyện, nhịp, máy quay, âm thanh, màu.</p>
          </div>
        </div>
        {skills.data?.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{skills.data.map((s) => <SkillCard key={s.slug} s={s} onHide={() => hide.mutateAsync({ kind: 'skills', item: s.slug }).catch(() => {})} />)}</div>
        ) : skills.isLoading ? <Skeleton className="h-40 rounded-xl" />
          : skills.error ? <p className="text-sm text-muted-foreground">Chưa tải được.</p>
          : <p className="text-sm text-muted-foreground">Chưa có phong cách nào. Học một video mẫu rồi tạo phong cách từ kết quả.</p>}
      </section>

      <section>
        <div className="mb-2 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Video mẫu đã học</h2>
            <p className="text-sm text-muted-foreground">Video dài nhiều tập mà Claude đã xem, nghe và rút ra cốt truyện + cách làm phim.</p>
          </div>
          <Button render={<Link to="/videos/new" />} variant="outline" size="sm" className="gap-1.5"><Plus className="size-3.5" /> Học video mẫu</Button>
        </div>
        <div className="divide-y rounded-xl border bg-card px-4">
          {analyses.data?.length ? analyses.data.map((a) => <AnalysisRow key={a.id} a={a} onHide={() => hide.mutate({ kind: 'runs', item: a.id })} />)
            : <p className="py-4 text-sm text-muted-foreground">{analyses.isLoading ? 'Đang tải…' : analyses.error ? 'Chưa tải được.' : 'Chưa có video mẫu nào.'}</p>}
        </div>
      </section>

      <footer className="flex justify-between border-t pt-6">
        <HiddenDialog />
        <a href={legacy.home} className="text-sm text-muted-foreground hover:text-foreground">Giao diện cũ</a>
      </footer>
    </main>
  )
}
