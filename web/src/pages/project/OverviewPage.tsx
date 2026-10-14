import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, CheckCircle2, Clock, Download, Film, ListChecks, PenLine, Shirt, X } from 'lucide-react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { api, type Project } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

const STEPS = ['Outline', 'Duyệt outline', 'Viết & góp ý từng tập', 'Chốt season']

function currentStep(p: Project): number {
  if (p.final_complete) return 4
  if (p.final_stale?.length) return 3
  if (p.episodes.length && !p.missing.length) return 2
  if (p.docs.outline.length) return 1
  return 0
}

function Stepper({ step }: { step: number }) {
  return (
    <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {STEPS.map((label, i) => {
        const done = i < step, now = i === step
        return (
          <li key={label} className={cn('flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm',
            done && 'border-success/30 bg-success/5', now && 'border-primary/40 bg-primary/5 font-medium')}>
            <span className={cn('flex size-6 shrink-0 items-center justify-center rounded-full text-xs',
              done ? 'bg-success text-white' : now ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>
              {done ? <Check className="size-3.5" /> : i + 1}
            </span>
            {label}
          </li>
        )
      })}
    </ol>
  )
}

function NextAction({ p }: { p: Project }) {
  const qc = useQueryClient()
  const run = useMutation({
    mutationFn: (approve: 'outline' | 'final') => api.refine(p.slug, p.session_id, { approve }),
    onSuccess: () => {
      askNotificationPermission()
      toast.success('Đã bắt đầu. Bạn có thể rời trang, xong sẽ có thông báo.')
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const shots = useMutation({
    mutationFn: () => api.makeShotlist(p.slug, p.session_id),
    onSuccess: () => {
      askNotificationPermission()
      toast.success('Claude đang tạo prompt video. Nút tải hiện ở từng tập khi xong.')
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const refresh = useMutation({
    mutationFn: () => api.refreshFinal(p.slug, p.session_id),
    onSuccess: (r) => {
      toast.success(`Đã chốt lại ${r.copied.length} file.`)
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const rewrite = useMutation({
    mutationFn: () => api.archiveEpisodes(p.slug, p.session_id, { rewrite: true }),
    onSuccess: (r) => {
      askNotificationPermission()
      toast.success(`Đã cất ${r.archived.length} tập cũ vào ${r.dir}. Claude đang viết lại từ tập 1.`)
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const busy = !!p.job
  // Drafts only: finalized or produced episodes are never taken out
  const canRewrite = p.episodes.length > 0 && !p.episodes.some((e) => e.in_final || e.produced)
  const planned = p.planned || p.episodes.length
  const rewriteAction = canRewrite && (
    <ConfirmAction trigger={<Button variant="outline">Xóa các tập đã viết, viết lại từ tập 1</Button>}
      title="Viết lại toàn bộ các tập?"
      description={<>Các tập {p.episodes.map((e) => e.n).join(', ')} được cất vào thư mục lưu trữ của series (không mất, khôi phục
        bằng tay được), góp ý trên các tập đó không dùng nữa. Claude viết lại {planned} tập liền mạch từ tập 1 theo outline
        hiện tại và phong cách mới nhất (khoảng {planned * 2}–{planned * 3} phút).</>}
      confirmLabel="Xóa và viết lại" pending={rewrite.isPending} onConfirm={() => rewrite.mutateAsync()} />
  )
  const range = p.missing.length ? `tập ${p.missing[0]}${p.missing.length > 1 ? `–${p.missing.at(-1)}` : ''}` : ''

  let title: string, body: React.ReactNode, action: React.ReactNode = null
  if (busy) {
    title = 'Đang xử lý'
    body = 'Có việc đang chạy cho series này. Khi xong trang sẽ tự cập nhật.'
  } else if (p.final_stale?.length) {
    const eps = p.final_stale.filter((x): x is number => typeof x === 'number')
    const docs = p.final_stale.filter((x) => typeof x === 'string').map((x) => (x === 'assets' ? 'bộ ngoại hình' : x))
    title = 'Có sửa sau khi chốt season'
    body = <>Bản chốt (dùng để tạo prompt video) đang cũ hơn bản đang sửa: {[...docs, ...(eps.length ? [`tập ${eps.join(', ')}`] : [])].join(', ')}.
      Đọc lại các tập này; ổn thì bấm “Chốt lại” để đưa bản mới vào bản chốt. Prompt video của các tập đó sẽ được đánh dấu cần tạo lại{p.final_stale.includes('assets') ? ' (bộ ngoại hình đổi: mọi tập)' : ''}.</>
    action = (
      <ConfirmAction trigger={<Button>Chốt lại {p.final_stale.length} mục</Button>} title="Chốt lại các thay đổi?"
        description="Bản mới nhất của các mục trên được chép vào bản chốt (final/). Không gọi Claude, xong ngay. Bản chốt cũ được thay bằng bản mới; các phiên bản nháp vẫn giữ nguyên."
        confirmLabel="Chốt lại" pending={refresh.isPending} onConfirm={() => refresh.mutateAsync()} />
    )
  } else if (p.final_complete) {
    const noPrompts = p.episodes.filter((e) => e.in_final && (!e.has_prompts || e.prompts_stale || e.prompts_outdated)).length
    title = 'Season đã chốt'
    body = noPrompts
      ? <>Bước tiếp: tạo prompt video cho {noPrompts} tập (Claude chia mỗi tập thành các clip 10–15s, mỗi clip một prompt có sẵn các cảnh cắt bên trong, kèm ảnh tham chiếu đã duyệt). Xong, mỗi thẻ tập có nút “Tải gói video”.</>
      : 'Mọi tập đã có prompt video: tải gói video ở từng thẻ tập bên dưới.'
    action = (
      <div className="flex flex-wrap gap-2">
        {noPrompts > 0 && (
          <ConfirmAction trigger={<Button>Tạo prompt video ({noPrompts} tập)</Button>} title="Tạo prompt video?"
            description={<>Claude tạo shotlist + prompt cho {noPrompts} tập chưa có prompt, có prompt cũ hoặc theo định dạng cũ (khoảng {Math.ceil(noPrompts / 4) * 5}–{Math.ceil(noPrompts / 4) * 10} phút). Nên duyệt ảnh nhân vật / bối cảnh trước để prompt gắn ảnh tham chiếu.</>}
            confirmLabel="Tạo" pending={shots.isPending} onConfirm={() => shots.mutateAsync()} />
        )}
        <Button render={<a href={`/series/${p.slug}/${p.session_id}/export`} />} variant="outline">Tải file biên kịch .md</Button>
      </div>
    )
  } else if (p.docs.outline.length && p.missing.length) {
    title = 'Đọc outline rồi duyệt'
    body = <>Duyệt xong, Claude viết {range} theo outline (khoảng {p.missing.length * 2}–{p.missing.length * 3} phút). Chưa ổn thì góp ý ở trang Outline.</>
    action = (
      <ConfirmAction trigger={<Button>Duyệt outline → viết {range}</Button>} title="Duyệt outline?"
        description={<>Claude sẽ viết {range}. Tập đã có không bị viết lại. Sau đó vẫn góp ý từng tập được.</>}
        confirmLabel="Duyệt và viết" pending={run.isPending} onConfirm={() => run.mutateAsync('outline')} />
    )
    if (rewriteAction) action = <div className="flex flex-wrap gap-2">{action}{rewriteAction}</div>
  } else if (p.episodes.length && !p.missing.length) {
    title = 'Đọc và góp ý từng tập'
    body = 'Mở từng tập ở cột trái. Khi mọi tập đã ổn, chốt season để lưu bản cuối.'
    action = (
      <ConfirmAction trigger={<Button variant="outline">Chốt season</Button>} title="Chốt season?"
        description="Bản mới nhất của mọi tập được lưu thành bản cuối (final/)." confirmLabel="Chốt season"
        pending={run.isPending} onConfirm={() => run.mutateAsync('final')} />
    )
    if (rewriteAction) action = <div className="flex flex-wrap gap-2">{action}{rewriteAction}</div>
  } else {
    title = 'Chưa có outline'
    body = 'Claude đang hoặc chưa viết outline cho series này.'
  }
  return (
    <div className="rounded-xl border bg-card p-5">
      <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Bước tiếp theo</div>
      <h2 className="mt-1 text-lg font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

const REQUIREMENTS = [
  'Trọn vẹn từ mở đầu đến kết (happy / bad)',
  'Cốt truyện chính',
  'Nhân vật chính và nhân vật phụ xoay quanh',
  'Lời thoại của các nhân vật',
  'Bối cảnh rõ ràng và cách bối cảnh thay đổi',
  'Cao trào',
  'Bí mật, bí ẩn: mở → manh mối → lời giải',
]

function StoryCheckCard({ p }: { p: Project }) {
  const qc = useQueryClient()
  const fix = useMutation({
    mutationFn: () => api.fixStory(p.slug, p.session_id),
    onSuccess: () => {
      toast.success('Claude đang sửa cốt truyện. Xong sẽ có thông báo.')
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  const c = p.story_check
  if (!c) return null
  const byReq = REQUIREMENTS.map((_, i) => c.errors.filter((e) => e.startsWith(`[R${i + 1}]`)))
  return (
    <section className="rounded-xl border bg-card p-5 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <ListChecks className="size-4" /> Kiểm tra cốt truyện
          <span className="font-normal text-muted-foreground">({c.stage === 'outline' ? 'bible + outline' : 'bible + outline + các tập'})</span>
        </div>
        {!c.ok && !p.job && (
          <ConfirmAction trigger={<Button size="sm">Sửa tự động</Button>} title="Sửa cốt truyện?"
            description={<>Claude sửa {c.errors.length} lỗi, ghi phiên bản mới cho bible / outline / các tập liên quan. Bản cũ được giữ.</>}
            confirmLabel="Sửa" pending={fix.isPending} onConfirm={() => fix.mutateAsync()} />
        )}
      </div>
      <ul className="mt-3 space-y-1.5">
        {REQUIREMENTS.map((label, i) => (
          <li key={label}>
            <details className="group">
              <summary className={cn('flex cursor-pointer list-none items-center gap-2', !byReq[i].length && 'cursor-default')}>
                {byReq[i].length
                  ? <X className="size-4 shrink-0 text-destructive" />
                  : <Check className="size-4 shrink-0 text-success" />}
                <span>{label}</span>
                {byReq[i].length > 0 && <span className="text-xs text-muted-foreground">{byReq[i].length} lỗi</span>}
              </summary>
              {byReq[i].length > 0 && (
                <ul className="mt-1 ml-6 list-disc space-y-0.5 pl-4 text-xs text-muted-foreground">
                  {byReq[i].map((e) => <li key={e}>{e.replace(/^\[R\d\] /, '')}</li>)}
                </ul>
              )}
            </details>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function OverviewPage() {
  const p = useProject()
  const base = `/p/${p.slug}/${p.session_id}`
  return (
    <div className="space-y-6">
      <Stepper step={currentStep(p)} />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <NextAction p={p} />
        <div className="rounded-xl border bg-card p-5 text-sm">
          <div className="flex items-center gap-2 font-medium"><Shirt className="size-4" /> Ngoại hình</div>
          {p.assets ? (
            <p className="mt-2 text-muted-foreground">
              Kho {p.assets.file}: {p.assets.counts.approved ?? 0} ảnh đã duyệt, {p.assets.counts.draft ?? 0} chờ duyệt,
              {' '}{p.assets.issues} lỗi liên tục.
            </p>
          ) : <p className="mt-2 text-muted-foreground">Chưa lập kho nhân vật & bối cảnh.</p>}
          <Link to={`${base}/looks/${p.assets?.counts.draft ? 'review' : 'characters'}`} className="mt-3 inline-block text-primary hover:underline">
            {!p.assets ? 'Lập kho' : p.assets.counts.draft ? `Duyệt ${p.assets.counts.draft} ảnh` : 'Mở nhân vật & bối cảnh'} →
          </Link>
        </div>
      </div>

      <StoryCheckCard p={p} />

      {p.editor && (
        <Link to={`${base}/editor`} className="flex flex-wrap items-center gap-3 rounded-xl border bg-card p-5 text-sm transition hover:border-primary/40">
          <PenLine className="size-4" />
          <span className="font-medium">Biên tập kịch bản</span>
          <span className={cn('font-semibold tabular-nums', p.editor.verdict === 'pass' ? 'text-success' : 'text-warning')}>
            {p.editor.average.toFixed(1)}/5 · {p.editor.verdict === 'pass' ? 'Đạt' : 'Cần sửa'}
          </span>
          <span className="text-muted-foreground">
            {p.editor.findings.high} nặng, {p.editor.findings.medium} vừa, {p.editor.findings.low} nhẹ
            {p.editor.applied ? ` · đã sửa ${p.editor.applied}` : ''}{p.editor.stale ? ' · kịch bản đã đổi, nên biên tập lại' : ''}
          </span>
          <span className="ml-auto text-primary">Mở →</span>
        </Link>
      )}

      <section>
        <h2 className="mb-3 text-base font-semibold">Các tập</h2>
        {p.episodes.length ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {p.episodes.map((e) => (
              <div key={e.n} className="flex flex-col rounded-xl border bg-card transition hover:border-primary/40 hover:shadow-sm">
              <Link to={`${base}/ep/${e.n}`} className="group flex-1 p-4">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-medium tabular-nums">TẬP {String(e.n).padStart(2, '0')}</span>
                  <span className="flex items-center gap-2">
                    {e.duration_sec != null && <span className="flex items-center gap-1"><Clock className="size-3" />{e.duration_sec}s</span>}
                    <span>v{e.versions.at(-1) ?? 1}</span>
                    {e.in_final && <CheckCircle2 className="size-3.5 text-success" />}
                    {e.produced && <Film className="size-3.5" />}
                  </span>
                </div>
                <h3 className="mt-1.5 font-semibold group-hover:text-primary">{e.title ?? `Tập ${e.n}`}</h3>
                {e.logline && <p className="mt-1 line-clamp-3 text-sm text-muted-foreground">{e.logline}</p>}
              </Link>
              {e.has_prompts && (
                <a href={api.packageUrl(p.slug, p.session_id, e.n)} download
                  className={cn('inline-flex items-center gap-1 border-t px-4 py-2 text-xs hover:underline', e.prompts_stale ? 'text-warning' : 'text-primary')}>
                  <Download className="size-3" /> {e.prompts_stale ? 'Gói video (prompt cũ, nên tạo lại)' : 'Tải gói video (Higgsfield)'}
                </a>
              )}
              </div>
            ))}
          </div>
        ) : <p className="text-sm text-muted-foreground">Chưa có tập nào. Duyệt outline để Claude bắt đầu viết.</p>}
      </section>
    </div>
  )
}
