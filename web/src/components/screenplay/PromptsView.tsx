import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Check, Copy, Download } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { thumb } from '@/components/looks/ImageTile'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api, type PromptShot } from '@/lib/api'
import { fmtDate } from '@/lib/format'

async function copy(text: string, what: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`Đã sao chép ${what}.`)
  } catch {
    toast.error('Trình duyệt không cho sao chép. Bôi đen rồi Ctrl+C.')
  }
}

const sec = (s: number | null | undefined) => (s == null ? '?' : `${Number(s).toFixed(1)}s`)

function ShotCard({ s, imgBase, names, unit }: { s: PromptShot; imgBase: string; names: Record<string, string>; unit: string }) {
  const [done, setDone] = useState(false)
  return (
    <article className="rounded-xl border bg-card">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b px-4 py-2.5 text-sm">
        <span className="rounded-md bg-foreground px-1.5 py-0.5 font-mono text-xs text-background">#{s.shot_number}</span>
        <span className="font-mono text-xs text-muted-foreground">{sec(s.start_sec)}–{sec(s.end_sec)} · {sec(s.duration_sec)}</span>
        <span className="text-xs text-muted-foreground">{s.scene}{s.camera ? ` · ${s.camera}` : ''}</span>
        <Button size="xs" variant={done ? 'secondary' : 'outline'} className="ml-auto gap-1"
          onClick={async () => { await copy(s.video_prompt || '', `prompt ${unit} ${s.shot_number}`); setDone(true) }}>
          {done ? <Check className="size-3" /> : <Copy className="size-3" />} Sao chép prompt
        </Button>
      </header>
      <div className="grid gap-4 p-4 md:grid-cols-[1fr_auto]">
        <div className="min-w-0 space-y-3 text-sm">
          {s.action && <p className="text-muted-foreground">{s.action}</p>}
          {s.continuity_in && <p className="text-xs text-muted-foreground">Nối tiếp clip trước: {s.continuity_in}</p>}
          {s.cuts.length > 0 && (
            <ol className="space-y-0.5 rounded-lg border px-3 py-2 text-xs">
              {s.cuts.map((c) => (
                <li key={c.cut} className="flex gap-2">
                  <span className="shrink-0 font-mono text-muted-foreground">{sec(c.start_sec)}–{sec(c.end_sec)}</span>
                  <span><b className="font-medium">{c.camera}</b>{c.action ? ` · ${c.action}` : ''}</span>
                </li>
              ))}
            </ol>
          )}
          {s.dialogue?.length > 0 && (
            <div className="space-y-1">
              {s.dialogue.map((d, i) => (
                <p key={i}>
                  {d.start_sec != null && <span className="mr-1 font-mono text-xs text-muted-foreground">{sec(d.start_sec)}</span>}
                  <span className="font-medium">{names[d.character] || d.character}</span>
                  {d.voiceover && <span className="ml-1 rounded bg-muted px-1 text-[10px] font-medium">VO</span>}
                  {d.delivery && <span className="ml-1 text-xs text-muted-foreground italic">({d.delivery})</span>}
                  <span className="ml-1">“{d.line}”</span>
                </p>
              ))}
            </div>
          )}
          <pre className="max-h-64 overflow-y-auto rounded-lg bg-muted/60 p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap">{s.video_prompt}</pre>
          {s.sfx && <p className="text-xs text-muted-foreground">Âm thanh: {s.sfx}</p>}
          {s.pace_warning.map((w, i) => (
            <p key={i} className="flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-400">
              <AlertTriangle className="mt-0.5 size-3 shrink-0" />{w}
            </p>
          ))}
        </div>
        <div className="flex flex-wrap content-start gap-2 md:w-44">
          <div className="w-full text-xs font-medium text-muted-foreground">Ảnh tham chiếu ({s.refs.length})</div>
          {s.refs.length ? s.refs.map((r) => (
            <a key={r} href={`${imgBase}/${r}`} target="_blank" rel="noreferrer" title={r}
              className="block size-20 overflow-hidden rounded-md border bg-muted">
              <img loading="lazy" src={thumb(imgBase, r, 200)} alt={r} className="size-full object-cover" />
            </a>
          )) : <p className="text-xs text-muted-foreground">Chưa có ảnh đã duyệt cho shot này.</p>}
        </div>
      </div>
    </article>
  )
}

/** The episode's video prompts (final/shots/epNN/prompts.json), one card per shot. */
export function PromptsView({ slug, sid, n }: { slug: string; sid: string; n: number }) {
  const q = useQuery({ queryKey: ['prompts', slug, sid, n], queryFn: () => api.prompts(slug, sid, n) })
  if (q.isLoading) return <div className="space-y-3"><Skeleton className="h-16" /><Skeleton className="h-48" /><Skeleton className="h-48" /></div>
  if (q.error || !q.data) return <p className="text-sm text-muted-foreground">{(q.error as Error)?.message || 'Chưa có prompt video.'}</p>
  const v = q.data
  const imgBase = `/series/${slug}/${sid}/assets`
  const unit = v.unit === 'clip' ? 'clip' : 'shot'
  const cuts = v.shots.reduce((k, s) => k + s.cuts.length, 0)
  const all = v.shots.map((s) => `#${s.shot_number} (${sec(s.start_sec)}-${sec(s.end_sec)})\n${s.video_prompt}`).join('\n\n')
  const noRefs = v.shots.filter((s) => !s.refs.length).length
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border bg-card px-4 py-2.5 text-sm">
        <span><b>{v.shots.length}</b> {unit}{cuts ? ` (${cuts} cảnh cắt)` : ''} · {v.total_duration_sec}s · {v.aspect_ratio}</span>
        <span className="text-xs text-muted-foreground">tạo {fmtDate(v.built_at)}</span>
        {noRefs > 0 && <span className="text-xs text-amber-700 dark:text-amber-400">{noRefs} {unit} chưa có ảnh tham chiếu</span>}
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => copy(all, `${v.shots.length} prompt`)}>
            <Copy className="size-3.5" /> Sao chép tất cả
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" render={<a href={api.packageUrl(slug, sid, n)} download />}>
            <Download className="size-3.5" /> Tải gói video
          </Button>
        </div>
      </div>
      {v.unit !== 'clip' ? (
        <p className="flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
          <AlertTriangle className="size-4 shrink-0" />
          Prompt kiểu cũ: mỗi shot 1–5s là một video riêng, dễ lệch mặt, trang phục và cắt vụn hội thoại. Bấm “Tạo prompt video”
          để tạo lại thành các clip 10–15s.
        </p>
      ) : v.stale && (
        <p className="flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
          <AlertTriangle className="size-4 shrink-0" />
          Prompt này tạo từ bản chốt cũ hơn (tập hoặc bộ ngoại hình đã chốt lại sau đó). Tạo lại prompt trước khi quay.
        </p>
      )}
      {v.check && v.check.errors.length > 0 && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-2.5 text-sm text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
          <p className="flex items-center gap-2 font-medium"><AlertTriangle className="size-4 shrink-0" />
            {v.check.errors.length} lỗi chia clip: tạo lại prompt video tập này.</p>
          <ul className="mt-1 list-disc pl-6 text-xs">{v.check.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        </div>
      )}
      {v.check && !v.check.errors.length && (
        <p className="text-xs text-muted-foreground">Đã kiểm tra: mỗi clip nằm trong đúng một cảnh (một bối cảnh, một thời điểm), tối đa 15s, thoại khớp thời gian.</p>
      )}
      {v.style_suffix && (
        <details className="rounded-lg border bg-card px-4 py-2.5 text-sm">
          <summary className="cursor-pointer text-muted-foreground">Phong cách hình chung (gắn cuối mỗi prompt)</summary>
          <p className="mt-2 font-mono text-xs">{v.style_suffix}</p>
        </details>
      )}
      {v.shots.map((s) => <ShotCard key={s.shot_number} s={s} imgBase={imgBase} names={v.names} unit={unit} />)}
    </div>
  )
}
