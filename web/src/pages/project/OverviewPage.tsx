import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, CheckCircle2, Clock, Film, Shirt } from 'lucide-react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { api, legacy, type Project } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

const STEPS = ['Outline', 'Duyệt outline', 'Viết & góp ý từng tập', 'Chốt season']

function currentStep(p: Project): number {
  if (p.final_complete) return 4
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
  const busy = !!p.job
  const range = p.missing.length ? `tập ${p.missing[0]}${p.missing.length > 1 ? `–${p.missing.at(-1)}` : ''}` : ''

  let title: string, body: React.ReactNode, action: React.ReactNode = null
  if (busy) {
    title = 'Đang xử lý'
    body = 'Có việc đang chạy cho series này. Khi xong trang sẽ tự cập nhật.'
  } else if (p.final_complete) {
    title = 'Season đã chốt'
    body = 'Bản cuối nằm trong thư mục final/. Có thể tải file biên kịch, hoặc lập kho ngoại hình để sản xuất.'
    action = <Button render={<a href={`/series/${p.slug}/${p.session_id}/export`} />} variant="outline">Tải file biên kịch .md</Button>
  } else if (p.docs.outline.length && p.missing.length) {
    title = 'Đọc outline rồi duyệt'
    body = <>Duyệt xong, Claude viết {range} theo outline (khoảng {p.missing.length * 2}–{p.missing.length * 3} phút). Chưa ổn thì góp ý ở trang Outline.</>
    action = (
      <ConfirmAction trigger={<Button>Duyệt outline → viết {range}</Button>} title="Duyệt outline?"
        description={<>Claude sẽ viết {range}. Tập đã có không bị viết lại. Sau đó vẫn góp ý từng tập được.</>}
        confirmLabel="Duyệt và viết" pending={run.isPending} onConfirm={() => run.mutateAsync('outline')} />
    )
  } else if (p.episodes.length && !p.missing.length) {
    title = 'Đọc và góp ý từng tập'
    body = 'Mở từng tập ở cột trái. Khi mọi tập đã ổn, chốt season để lưu bản cuối.'
    action = (
      <ConfirmAction trigger={<Button variant="outline">Chốt season</Button>} title="Chốt season?"
        description="Bản mới nhất của mọi tập được lưu thành bản cuối (final/)." confirmLabel="Chốt season"
        pending={run.isPending} onConfirm={() => run.mutateAsync('final')} />
    )
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
          <a href={legacy.project(p.slug, p.session_id, p.assets ? 'chars' : '')} className="mt-3 inline-block text-primary hover:underline">
            {p.assets ? 'Mở nhân vật & bối cảnh' : 'Lập kho'} →
          </a>
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-base font-semibold">Các tập</h2>
        {p.episodes.length ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {p.episodes.map((e) => (
              <Link key={e.n} to={`${base}/ep/${e.n}`}
                className="group rounded-xl border bg-card p-4 transition hover:border-primary/40 hover:shadow-sm">
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
            ))}
          </div>
        ) : <p className="text-sm text-muted-foreground">Chưa có tập nào. Duyệt outline để Claude bắt đầu viết.</p>}
      </section>
    </div>
  )
}
