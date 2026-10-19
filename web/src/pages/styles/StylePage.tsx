import { useMutation, useQuery } from '@tanstack/react-query'
import { Check, Film, Languages, PenLine, X } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { toast } from 'sonner'
import { Markdown } from '@/components/Markdown'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk } from '@/lib/api'
import { fmtDate } from '@/lib/format'

const RULES: [string, string][] = [['story', 'Cấu trúc truyện'], ['characters', 'Nhân vật'], ['pacing', 'Nhịp'], ['camera', 'Máy quay'], ['sound', 'Âm thanh'], ['color', 'Màu & ánh sáng']]

export function StylePage() {
  const { slug = '' } = useParams()
  const { data: s, isLoading, error } = useQuery({ queryKey: qk.skill(slug), queryFn: () => api.skill(slug) })
  const summarize = useMutation({
    mutationFn: () => api.summarize('skill', slug),
    onSuccess: () => toast.success('Claude đang viết tóm tắt tiếng Việt (1–3 phút).'),
    onError: (e) => toast.error((e as Error).message),
  })
  if (error) return <main className="mx-auto max-w-5xl p-10 text-destructive">{(error as Error).message}</main>
  if (isLoading || !s) return <main className="mx-auto max-w-5xl space-y-4 p-10"><Skeleton className="h-24" /><Skeleton className="h-96" /></main>
  const vi = s.summary_vi
  return (
    <main className="mx-auto max-w-6xl space-y-5 px-4 py-8">
      <div>
        <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">← Dự án</Link>
        <div className="mt-1 flex flex-wrap items-start gap-3">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">Phong cách {s.slug}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{s.version} · lệnh <code>/{s.name}</code>{s.projects.length ? ` · ${s.projects.length} series` : ''}</p>
          </div>
          <Button render={<Link to={`/new?skill=${s.slug}`} />} className="gap-1.5"><PenLine className="size-4" /> Viết series với phong cách này</Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          {vi ? (
            <>
              <section className="rounded-xl border bg-card p-6">
                {vi.tagline_vi && <p className="text-lg leading-relaxed font-medium">{vi.tagline_vi}</p>}
                {vi.description_vi && <p className="mt-3 leading-relaxed text-muted-foreground">{vi.description_vi}</p>}
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {vi.best_for_vi?.length ? (
                    <div><div className="text-sm font-medium">Hợp với</div>
                      <ul className="mt-1.5 space-y-1 text-sm">{vi.best_for_vi.map((x) => <li key={x} className="flex gap-2"><Check className="mt-0.5 size-4 shrink-0 text-success" />{x}</li>)}</ul></div>
                  ) : null}
                  {vi.not_for_vi?.length ? (
                    <div><div className="text-sm font-medium">Không hợp với</div>
                      <ul className="mt-1.5 space-y-1 text-sm">{vi.not_for_vi.map((x) => <li key={x} className="flex gap-2"><X className="mt-0.5 size-4 shrink-0 text-muted-foreground" />{x}</li>)}</ul></div>
                  ) : null}
                </div>
                {s.summary_stale && <p className="mt-4 text-xs text-warning">Tóm tắt viết cho phiên bản cũ ({vi.version}); phong cách đã lên {s.version}.</p>}
              </section>
              <section className="rounded-xl border bg-card p-6">
                <h2 className="font-semibold">Luật chính</h2>
                <div className="mt-4 grid gap-5 md:grid-cols-2">
                  {RULES.map(([k, label]) => vi.rules_vi?.[k]?.length ? (
                    <div key={k}>
                      <div className="text-xs font-semibold tracking-wide text-primary uppercase">{label}</div>
                      <ul className="mt-1.5 list-disc space-y-1 pl-4 text-sm">{vi.rules_vi[k].map((r) => <li key={r}>{r}</li>)}</ul>
                    </div>
                  ) : null)}
                </div>
              </section>
            </>
          ) : (
            <section className="rounded-xl border bg-card p-6">
              <p className="text-muted-foreground">{s.description}</p>
              <div className="mt-4 flex flex-wrap items-center gap-3 rounded-lg bg-muted/50 p-4 text-sm">
                <Languages className="size-5 text-muted-foreground" />
                <span className="flex-1">Phong cách được viết bằng tiếng Anh. Tạo bản tóm tắt tiếng Việt: dùng cho ý tưởng nào, các luật chính.</span>
                <Button size="sm" disabled={summarize.isPending} onClick={() => summarize.mutate()}>Tạo tóm tắt tiếng Việt</Button>
              </div>
            </section>
          )}
          <details className="rounded-xl border bg-card">
            <summary className="cursor-pointer px-6 py-4 text-sm font-medium">Toàn bộ skill (SKILL.md, tiếng Anh)</summary>
            <div className="border-t px-6 py-5"><Markdown>{s.skill_md.replace(/^---[\s\S]*?---\n/, '')}</Markdown></div>
          </details>
        </div>

        <aside className="space-y-4">
          {s.reference && (
            <section className="rounded-xl border bg-card p-5 text-sm">
              <h3 className="font-semibold">Học từ video</h3>
              <Link to={`/videos/${s.reference.id}`} className="mt-2 flex items-center gap-2 text-primary hover:underline">
                <Film className="size-4" />{s.reference.title || s.reference.id} ({s.reference.minutes} phút)
              </Link>
            </section>
          )}
          <section className="rounded-xl border bg-card p-5 text-sm">
            <h3 className="font-semibold">Phiên bản</h3>
            <ol className="mt-3 space-y-3 border-l pl-4">
              {[...s.versions].reverse().map((v) => (
                <li key={v.version} className="relative">
                  <span className="absolute top-1.5 -left-[21px] size-2.5 rounded-full border-2 border-card bg-primary" />
                  <div className="flex items-center gap-2"><b>{v.version}</b>{v.version === s.version && <StatusBadge tone="run">đang dùng</StatusBadge>}
                    {v.stable && <StatusBadge tone="ok">ổn định</StatusBadge>}</div>
                  <div className="text-xs text-muted-foreground">{fmtDate(v.created)}</div>
                  {v.changes.length ? <ul className="mt-1 list-disc pl-4 text-xs text-muted-foreground">{v.changes.map((c) => <li key={c}>{c}</li>)}</ul> : null}
                </li>
              ))}
            </ol>
          </section>
          {s.projects.length > 0 && (
            <section className="rounded-xl border bg-card p-5 text-sm">
              <h3 className="font-semibold">Series dùng phong cách này</h3>
              <ul className="mt-2 space-y-1">{s.projects.map((p) => (
                <li key={p.session_id}><Link to={`/p/${p.slug}/${p.session_id}`} className="text-primary hover:underline">{p.title}</Link></li>
              ))}</ul>
            </section>
          )}
          {vi && <button className="text-xs text-muted-foreground hover:text-foreground" disabled={summarize.isPending} onClick={() => summarize.mutate()}>Viết lại tóm tắt tiếng Việt</button>}
        </aside>
      </div>
    </main>
  )
}
