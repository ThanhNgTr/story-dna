import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, BookOpen, FileText, History, MessageSquareQuote, PenLine, RefreshCw, Home, Images, Lightbulb, ListOrdered, MapPin, Package, Shirt } from 'lucide-react'
import { Link, NavLink, Outlet, useOutletContext, useParams } from 'react-router'
import { StatusBadge } from '@/components/StatusBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk, type Project } from '@/lib/api'
import { STEP_LABEL, fmtEta } from '@/lib/format'
import { cn } from '@/lib/utils'

export function useProject() {
  return useOutletContext<Project>()
}

function SideLink({ to, icon: Icon, children, end, extra }: {
  to: string
  icon?: React.ComponentType<{ className?: string }>
  children: React.ReactNode
  end?: boolean
  extra?: React.ReactNode
}) {
  return (
    <NavLink to={to} end={end}
      className={({ isActive }) => cn('flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors',
        isActive ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground' : 'text-foreground/80 hover:bg-muted')}>
      {Icon && <Icon className="size-4 shrink-0 opacity-70" />}
      <span className="min-w-0 flex-1 truncate">{children}</span>
      {extra}
    </NavLink>
  )
}

function Group({ children }: { children: React.ReactNode }) {
  return <div className="mt-5 mb-1 px-2.5 text-[11px] font-medium tracking-wider text-muted-foreground uppercase">{children}</div>
}

export function ProjectLayout() {
  const { slug = '', sid = '' } = useParams()
  const { data: p, error } = useQuery({ queryKey: qk.project(slug, sid), queryFn: () => api.project(slug, sid) })
  const base = `/p/${slug}/${sid}`

  if (error) return <main className="mx-auto max-w-3xl p-10 text-destructive">{(error as Error).message}</main>
  if (!p) return (
    <main className="mx-auto max-w-[1500px] p-4"><Skeleton className="h-10 w-80" /><Skeleton className="mt-6 h-96" /></main>
  )
  const runningStep = p.job && Object.entries(p.job.steps).find(([, s]) => s.status === 'running')?.[0]

  return (
    <div className="mx-auto grid max-w-[1500px] gap-6 px-4 py-6 lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="lg:sticky lg:top-20 lg:max-h-[calc(100vh-6rem)] lg:overflow-y-auto">
        <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">← Dự án</Link>
        <h2 className="mt-2 text-lg leading-tight font-semibold">{p.title}</h2>
        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <StatusBadge tone={p.stage.tone}>{p.stage.label}</StatusBadge>
          <span>{p.input.episodes} tập × {p.input.episode_sec}s</span>
        </div>
        <nav className="mt-4">
          <SideLink to={base} end icon={Home}>Tổng quan</SideLink>
          <Group>Câu chuyện</Group>
          {p.docs.adaptation.length > 0 && <SideLink to={`${base}/doc/adaptation`} icon={Lightbulb}>Ghép ý tưởng</SideLink>}
          {p.docs.canon.length > 0 && <SideLink to={`${base}/doc/canon`} icon={FileText}>Đối chiếu video</SideLink>}
          {p.docs.bible.length > 0 && <SideLink to={`${base}/doc/bible`} icon={BookOpen}>Series bible</SideLink>}
          {p.docs.outline.length > 0 && <SideLink to={`${base}/doc/outline`} icon={ListOrdered}>Outline</SideLink>}
          {p.docs.outline.length > 0 && (
            <SideLink to={`${base}/editor`} icon={PenLine} extra={p.editor ? (
              <span className={cn('text-xs tabular-nums', p.editor.verdict === 'pass' ? 'text-success' : 'text-warning')}>
                {p.editor.average.toFixed(1)}
              </span>
            ) : undefined}>Biên tập</SideLink>
          )}
          {p.episodes.length > 0 && <SideLink to={`${base}/dialogue`} icon={MessageSquareQuote}>Lời thoại</SideLink>}
          <Group>Kịch bản</Group>
          {p.episodes.length ? p.episodes.map((e) => (
            <SideLink key={e.n} to={`${base}/ep/${e.n}`}
              extra={<span className="text-[11px] text-muted-foreground">v{e.versions.at(-1) ?? 1}</span>}>
              <span className="text-muted-foreground tabular-nums">{String(e.n).padStart(2, '0')}</span> {e.title ?? `Tập ${e.n}`}
            </SideLink>
          )) : <p className="px-2.5 text-sm text-muted-foreground">Chưa viết tập nào.</p>}
          <Group>Ngoại hình</Group>
          <SideLink to={`${base}/looks/characters`} icon={Shirt}>Nhân vật & trang phục</SideLink>
          <SideLink to={`${base}/looks/locations`} icon={MapPin}>Bối cảnh</SideLink>
          <SideLink to={`${base}/looks/props`} icon={Package}>Đạo cụ</SideLink>
          <SideLink to={`${base}/looks/review`} icon={Images}
            extra={p.assets?.counts.draft ? <span className="rounded-full bg-warning/15 px-1.5 text-[11px] text-warning">{p.assets.counts.draft}</span> : null}>Duyệt ảnh</SideLink>
          <SideLink to={`${base}/looks/issues`} icon={AlertTriangle}
            extra={p.assets?.issues ? <span className="text-[11px] text-muted-foreground">{p.assets.issues}</span> : null}>Lỗi liên tục</SideLink>
          <Group>Khác</Group>
          <SideLink to={`/continue?slug=${encodeURIComponent(slug)}&sid=${encodeURIComponent(sid)}`} icon={RefreshCw}>Viết tiếp từ video đã quay</SideLink>
          <SideLink to={`${base}/history`} icon={History} extra={p.iterations.length ?
            <span className="text-[11px] text-muted-foreground">{p.iterations.length}</span> : null}>Lịch sử góp ý</SideLink>
        </nav>
      </aside>
      <div className="min-w-0">
        {p.job && (
          <Link to={`/jobs/${p.job.id}`}
            className="mb-4 flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-2.5 text-sm hover:bg-primary/10">
            <span className="size-2 animate-pulse rounded-full bg-primary" />
            <span className="font-medium">{p.job.title}</span>
            {runningStep && <span className="text-muted-foreground">· {STEP_LABEL[runningStep] ?? runningStep}</span>}
            <span className="ml-auto text-primary">{fmtEta(p.job.eta_sec) ? `${fmtEta(p.job.eta_sec)} · ` : ''}Xem tiến độ →</span>
          </Link>
        )}
        <Outlet context={p} />
      </div>
    </div>
  )
}
