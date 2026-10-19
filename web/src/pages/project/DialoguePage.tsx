import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, MessageSquareQuote, Sparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk, type DialogueItem } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { fmtDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

const ISSUE: Record<string, { label: string; hint: string }> = {
  telegraphic: { label: 'Câu cụt', hint: 'Chuỗi cụm từ ngắn không đủ chủ vị, người xem phải tự đoán ý ("Một tấm rèm. Sáu căn nhà trả.")' },
  figure: { label: 'Quá nhiều ẩn dụ', hint: 'Hơn 2 câu so sánh "như..." trong một tập: lời dẫn thành câu đố' },
  pronoun: { label: 'Xưng hô lẫn', hint: 'Lời dẫn của cùng một người lúc xưng "tao" lúc xưng "tôi"' },
  clock: { label: 'Giờ kiểu máy', hint: 'Nhân vật nói "hai mươi hai giờ" thay vì "mười giờ tối"' },
  short_heavy: { label: 'Quá nhiều câu cực ngắn', hint: 'Hơn 55% câu thoại trong tập chỉ 1–3 từ' },
  definition: { label: 'Câu giải nghĩa', hint: 'Câu giảng nghĩa một từ cho khán giả ("Giàn giáo là khung ống thép...", "tức là", "gọi là"): người thật không nói vậy với nhau' },
  narrates_action: { label: 'Kể lại hình', hint: 'Lời dẫn kể đúng việc hình đang chiếu; lời dẫn chỉ nên nói điều hình không thể hiện (suy nghĩ, cảm xúc, bí mật)' },
}
const WHY: Record<string, string> = {
  telegraphic: 'câu cụt', riddle: 'câu đố', pronoun: 'xưng hô', term: 'thuật ngữ chưa giải thích', calque: 'dịch từ tiếng Anh',
  referent: '"nó / cái đó" không rõ', clock: 'cách nói giờ', definition: 'câu giải nghĩa',
  narrates_action: 'kể lại hình', other: 'khác',
}

function PolishButton({ episodes, label, variant = 'default', size = 'default' }: {
  episodes: number[]; label: string; variant?: 'default' | 'outline'; size?: 'default' | 'sm'
}) {
  const p = useProject()
  const qc = useQueryClient()
  const run = useMutation({
    mutationFn: () => api.polishDialogue(p.slug, p.session_id, episodes),
    onSuccess: () => {
      askNotificationPermission()
      toast.success('Claude đang làm rõ thoại. Bản cũ được giữ; xong sẽ có thông báo.')
      qc.invalidateQueries({ queryKey: qk.project(p.slug, p.session_id) })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const n = episodes.length || p.episodes.length
  return (
    <ConfirmAction trigger={<Button variant={variant} size={size} className="gap-1.5" disabled={!!p.job}><Sparkles className="size-3.5" />{label}</Button>}
      title="Làm rõ lời thoại?" confirmLabel="Làm rõ" pending={run.isPending} onConfirm={() => run.mutateAsync()}
      description={<>Claude viết lại thoại và lời dẫn của {episodes.length ? `tập ${episodes.join(', ')}` : 'tất cả các tập'} cho dễ hiểu, tự nhiên.
        Chỉ đổi câu chữ: cảnh, thời lượng, hành động giữ nguyên. Mỗi tập thành một phiên bản mới, so sánh được với bản cũ
        (khoảng {Math.max(3, n * 2)}–{Math.max(6, n * 4)} phút).</>} />
  )
}

export function DialoguePage() {
  const p = useProject()
  const base = `/p/${p.slug}/${p.session_id}`
  const { data, isLoading, error } = useQuery({ queryKey: qk.dialogue(p.slug, p.session_id), queryFn: () => api.dialogue(p.slug, p.session_id) })
  const [filter, setFilter] = useState<string>('')
  const byEp = useMemo(() => {
    const m = new Map<number, DialogueItem[]>()
    for (const it of data?.items ?? []) {
      if (filter && !it.issues.includes(filter)) continue
      m.set(it.episode, [...(m.get(it.episode) ?? []), it])
    }
    return [...m.entries()].sort((a, b) => a[0] - b[0])
  }, [data, filter])

  if (error) return <p className="text-sm text-muted-foreground">{(error as Error).message}</p>
  if (isLoading || !data) return <Skeleton className="h-96" />
  const total = data.items.length

  return (
    <div className="space-y-6">
      <div className="rounded-xl border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold"><MessageSquareQuote className="size-5" /> Lời thoại</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
              Máy dò những câu dễ gây khó hiểu (kiểm tra nhanh, chỉ là gợi ý). Bấm “Làm rõ thoại” để Claude viết lại cho rõ và tự nhiên,
              theo bộ quy tắc thoại tiếng Việt và theo cách bạn từng sửa tay.
            </p>
          </div>
          <PolishButton episodes={[]} label="Làm rõ thoại tất cả tập" />
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">
          <button onClick={() => setFilter('')}
            className={cn('rounded-full border px-3 py-1', !filter ? 'border-primary bg-primary/10 text-primary' : 'text-muted-foreground')}>
            Tất cả ({total})
          </button>
          {Object.entries(data.counts).map(([k, v]) => (
            <button key={k} onClick={() => setFilter(k)} title={ISSUE[k]?.hint}
              className={cn('rounded-full border px-3 py-1', filter === k ? 'border-primary bg-primary/10 text-primary' : 'text-muted-foreground')}>
              {ISSUE[k]?.label ?? k} ({v})
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          {data.examples
            ? <>Claude đang học từ <b className="text-foreground">{data.examples}</b> câu bạn đã sửa tay (Sửa trực tiếp ở trang tập).</>
            : <>Mỗi lần bạn sửa thoại bằng “Sửa trực tiếp”, câu trước / sau được lưu lại để Claude học cách bạn viết.</>}
        </p>
      </div>

      {data.last_polish?.changes?.length ? (
        <section className="rounded-xl border bg-card p-6">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-semibold">Lần làm rõ gần nhất ({data.last_polish.changes.length} câu)</h2>
            <span className="text-xs text-muted-foreground">{fmtDate(data.last_polish.created_at)} · mở trang tập, bấm “So sánh phiên bản” để xem trong bối cảnh</span>
          </div>
          <ul className="mt-4 divide-y">
            {data.last_polish.changes.slice(0, 60).map((c, i) => (
              <li key={i} className="grid gap-2 py-3 text-sm md:grid-cols-[90px_1fr_1fr]">
                <Link to={`${base}/ep/${c.episode}`} className="text-xs text-primary hover:underline">
                  Tập {c.episode}{c.scene ? ` · ${c.scene}` : ''}{c.name ? ` · ${c.name}` : ''}{c.voiceover ? ' (VO)' : ''}
                  {c.why && <span className="mt-0.5 block text-muted-foreground">{WHY[c.why] ?? c.why}</span>}
                </Link>
                <p className="rounded-md bg-destructive/5 px-3 py-2 font-serif text-muted-foreground line-through decoration-destructive/40">{c.before}</p>
                <p className="rounded-md bg-success/5 px-3 py-2 font-serif">{c.after}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-xl border bg-card p-6">
        <h2 className="font-semibold">Câu cần xem lại ({byEp.reduce((s, [, xs]) => s + xs.length, 0)})</h2>
        {byEp.length ? byEp.map(([ep, items]) => (
          <div key={ep} className="mt-5">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <Link to={`${base}/ep/${ep}`} className="flex items-center gap-1 text-sm font-medium hover:text-primary">
                Tập {ep}{p.episodes.find((e) => e.n === ep)?.title ? `: ${p.episodes.find((e) => e.n === ep)!.title}` : ''} <ArrowRight className="size-3.5" />
              </Link>
              <PolishButton episodes={[ep]} label={`Làm rõ thoại tập ${ep}`} variant="outline" size="sm" />
            </div>
            <ul className="space-y-1.5">
              {items.map((it, i) => (
                <li key={i} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 rounded-md px-3 py-2 text-sm hover:bg-muted/50">
                  <span className="w-12 shrink-0 font-mono text-xs text-muted-foreground">{it.scene ?? ''}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">{it.name ?? it.character}{it.voiceover ? ' (VO)' : ''}</span>
                  <span className="min-w-0 flex-1 font-serif">{it.line ?? it.note}</span>
                  <span className="flex gap-1">{it.issues.map((x) => (
                    <span key={x} title={ISSUE[x]?.hint} className="rounded bg-warning/10 px-1.5 py-0.5 text-xs text-warning">{ISSUE[x]?.label ?? x}</span>
                  ))}</span>
                </li>
              ))}
            </ul>
          </div>
        )) : <p className="mt-3 text-sm text-muted-foreground">Không có câu nào bị đánh dấu.</p>}
      </section>
    </div>
  )
}
