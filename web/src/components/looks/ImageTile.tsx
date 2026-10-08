import { Check, ChevronLeft, ChevronRight, Columns2, ImageOff, RefreshCw, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import type { AssetImage, AssetKind, ImgSet } from '@/lib/api'
import { fmtDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Looks } from './useLooks'

export const IMG_STATUS = {
  draft: { label: 'Chờ duyệt', tone: 'warn' },
  approved: { label: 'Đã duyệt', tone: 'ok' },
  rejected: { label: 'Đã bỏ', tone: 'muted' },
  old: { label: 'Bản cũ', tone: 'muted' },
} as const

export const thumb = (base: string, file: string, w = 480) => `${base}/${file}?w=${w}`
export const full = (base: string, file: string) => `${base}/${file}`

function Lightbox({ images, index, base, label, looks, onClose }: {
  images: AssetImage[]
  index: number
  base: string
  label: string
  looks: Looks
  onClose: () => void
}) {
  const [i, setI] = useState(index)
  const [compare, setCompare] = useState(false)
  const img = images[i]
  const other = images[i + 1] ?? images[i - 1]
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setI((x) => Math.min(images.length - 1, x + 1))
      if (e.key === 'ArrowLeft') setI((x) => Math.max(0, x - 1))
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [images.length])
  if (!img) return null
  const st = IMG_STATUS[img.status]
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-h-[95vh] w-[min(96vw,1400px)] max-w-none overflow-y-auto sm:max-w-none">
        <DialogTitle className="flex flex-wrap items-center gap-2 pr-8">
          {label} <StatusBadge tone={st.tone}>{st.label}</StatusBadge>
          <span className="text-xs font-normal text-muted-foreground">{img.name} · {fmtDate(img.created_at)}{img.sec ? ` · ${img.sec}s` : ''}</span>
        </DialogTitle>
        <div className={cn('grid gap-3', compare && other && 'md:grid-cols-2')}>
          <figure>
            <img src={full(base, img.file)} alt={label} className="max-h-[70vh] w-full rounded-lg bg-muted object-contain" />
          </figure>
          {compare && other && (
            <figure>
              <img src={full(base, other.file)} alt={`${label} (so sánh)`} className="max-h-[70vh] w-full rounded-lg bg-muted object-contain" />
              <figcaption className="mt-1 text-xs text-muted-foreground">{other.name} · {IMG_STATUS[other.status].label}</figcaption>
            </figure>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="ghost" disabled={i === 0} onClick={() => setI(i - 1)}><ChevronLeft className="size-4" /></Button>
          <span className="text-xs text-muted-foreground tabular-nums">{i + 1}/{images.length}</span>
          <Button size="sm" variant="ghost" disabled={i === images.length - 1} onClick={() => setI(i + 1)}><ChevronRight className="size-4" /></Button>
          {images.length > 1 && (
            <Button size="sm" variant={compare ? 'secondary' : 'outline'} className="gap-1.5" onClick={() => setCompare(!compare)}>
              <Columns2 className="size-3.5" /> So sánh cạnh nhau
            </Button>
          )}
          <div className="ml-auto flex gap-2">
            {img.status !== 'rejected' && (
              <Button size="sm" variant="outline" className="gap-1" onClick={() => looks.review.mutate({ files: [img.file], status: 'rejected' })}>
                <X className="size-3.5" /> Bỏ
              </Button>
            )}
            {img.status !== 'approved' && (
              <Button size="sm" className="gap-1 bg-success text-white hover:bg-success/90" onClick={() => looks.review.mutate({ files: [img.file], status: 'approved' })}>
                <Check className="size-3.5" /> Duyệt làm ảnh chuẩn
              </Button>
            )}
          </div>
        </div>
        {img.prompt && (
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground">Prompt đã dùng{img.refs?.length ? ` · ảnh tham chiếu: ${img.refs.join(', ')}` : ''}</summary>
            <pre className="mt-2 rounded-md bg-muted p-3 whitespace-pre-wrap">{img.prompt}</pre>
          </details>
        )}
      </DialogContent>
    </Dialog>
  )
}

/** Every image of one registry item (a character sheet, an outfit, a location variant, a prop). */
export function ImageSet({ id, kind, set, base, label, looks, busy, codex, aspect = 'landscape', empty }: {
  id: string
  kind: AssetKind
  set: ImgSet
  base: string
  label: string
  looks: Looks
  busy: boolean
  codex: boolean
  aspect?: 'landscape' | 'portrait' | 'square'
  empty?: React.ReactNode
}) {
  const [open, setOpen] = useState<number | null>(null)
  const imgs = set.images
  const ratio = aspect === 'portrait' ? 'aspect-[9/16]' : aspect === 'square' ? 'aspect-square' : 'aspect-[3/2]'
  return (
    <div>
      <div className={cn('grid gap-3', aspect === 'portrait' ? 'grid-cols-[repeat(auto-fill,minmax(140px,1fr))]' : 'grid-cols-[repeat(auto-fill,minmax(220px,1fr))]')}>
        {imgs.map((img, i) => {
          const st = IMG_STATUS[img.status]
          return (
            <figure key={img.file} className={cn('group overflow-hidden rounded-lg border bg-muted/40',
              img.status === 'approved' && 'ring-2 ring-success', img.status === 'rejected' && 'opacity-50')}>
              <button className={cn('block w-full overflow-hidden', ratio)} onClick={() => setOpen(i)} title="Xem lớn">
                <img loading="lazy" src={thumb(base, img.file)} alt={label} className="size-full object-cover transition group-hover:scale-[1.02]" />
              </button>
              <figcaption className="flex items-center gap-1.5 px-2 py-1.5">
                <StatusBadge tone={st.tone}>{st.label}</StatusBadge>
                <span className="ml-auto flex gap-0.5">
                  {img.status !== 'approved' && (
                    <Button size="icon-xs" variant="ghost" title="Duyệt" onClick={() => looks.review.mutate({ files: [img.file], status: 'approved' })}>
                      <Check className="size-3.5 text-success" />
                    </Button>
                  )}
                  {img.status !== 'rejected' && (
                    <Button size="icon-xs" variant="ghost" title="Bỏ" onClick={() => looks.review.mutate({ files: [img.file], status: 'rejected' })}>
                      <X className="size-3.5" />
                    </Button>
                  )}
                </span>
              </figcaption>
            </figure>
          )
        })}
        {!imgs.length && (
          <div className={cn('flex flex-col items-center justify-center gap-1 rounded-lg border border-dashed text-center text-xs text-muted-foreground', ratio)}>
            <ImageOff className="size-5" />
            {empty ?? 'Chưa có ảnh'}
          </div>
        )}
      </div>
      {set.error && <p className="mt-1.5 text-xs text-destructive">Lần tạo gần nhất bị lỗi: {set.error.slice(0, 200)}</p>}
      {codex && (
        <Button size="xs" variant="outline" className="mt-2 gap-1" disabled={busy || looks.generate.isPending}
          title={busy ? 'Đang có việc chạy cho series này' : undefined}
          onClick={() => looks.generate.mutate({ kinds: [kind], ids: [id], force: imgs.length > 0 })}>
          <RefreshCw className="size-3" /> {imgs.length ? 'Tạo ảnh khác' : 'Tạo ảnh'}
          <span className="font-normal text-muted-foreground">~2–4 phút</span>
        </Button>
      )}
      {open != null && <Lightbox images={imgs} index={open} base={base} label={label} looks={looks} onClose={() => setOpen(null)} />}
    </div>
  )
}

export function approvedOf(set: ImgSet): AssetImage | undefined {
  return set.images.find((i) => i.status === 'approved')
}
