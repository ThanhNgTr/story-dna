import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Clapperboard, Plus } from 'lucide-react'
import { Link } from 'react-router'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api, legacy, qk, type ProjectSummary } from '@/lib/api'

function ProjectCard({ p }: { p: ProjectSummary }) {
  const planned = p.planned || p.episodes || 1
  const pct = Math.min(100, Math.round((100 * (p.episodes + p.produced)) / planned))
  return (
    <Link to={`/p/${p.slug}/${p.session_id}`}
      className="group flex flex-col rounded-xl border bg-card p-5 shadow-xs transition hover:border-primary/40 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-lg font-semibold">{p.title}</h3>
          <p className="mt-0.5 text-sm text-muted-foreground">Phong cách {p.slug}</p>
        </div>
        <StatusBadge tone={p.stage.tone}>{p.stage.label}</StatusBadge>
      </div>
      <div className="mt-5">
        <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
          <span>{p.episodes} / {planned} tập đã viết{p.produced ? ` · ${p.produced} tập đã quay` : ''}</span>
          <span>{pct}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="mt-5 flex items-center justify-between text-sm">
        <span className="text-xs text-muted-foreground">{p.session_id}</span>
        <span className="flex items-center gap-1 font-medium text-primary opacity-80 group-hover:opacity-100">
          Mở <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
        </span>
      </div>
    </Link>
  )
}

export function ProjectsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: qk.projects, queryFn: api.projects })
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dự án của bạn</h1>
          <p className="mt-1 text-muted-foreground">Mỗi dự án là một series: ý tưởng, bible, outline, kịch bản và ngoại hình.</p>
        </div>
        <Button render={<a href={legacy.seriesNew} />} className="gap-1.5"><Plus className="size-4" /> Series mới</Button>
      </div>
      {error && <p className="text-destructive">Không tải được danh sách: {(error as Error).message}</p>}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-44 rounded-xl" />)}
        </div>
      ) : data?.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.map((p) => <ProjectCard key={p.slug + p.session_id} p={p} />)}</div>
      ) : (
        <div className="flex flex-col items-center rounded-xl border border-dashed px-6 py-16 text-center">
          <Clapperboard className="size-10 text-muted-foreground" />
          <h2 className="mt-4 text-lg font-medium">Chưa có dự án nào</h2>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            Học một video mẫu để có phong cách kể chuyện, rồi đưa ý tưởng của bạn vào để viết series 10–20 tập.
          </p>
          <div className="mt-6 flex gap-2">
            <Button render={<a href={legacy.analyzeNew} />} variant="outline">Học video mẫu</Button>
            <Button render={<a href={legacy.seriesNew} />}>Viết series mới</Button>
          </div>
        </div>
      )}
    </main>
  )
}
