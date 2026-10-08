import { diffWordsWithSpace } from 'diff'
import type { Beat, EpisodeData } from '@/lib/api'
import { fmtTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { nameOf, type CastMember } from './cast'

function Words({ a = '', b = '' }: { a?: string; b?: string }) {
  if (a === b) return <span>{b}</span>
  return (
    <span>
      {diffWordsWithSpace(a, b).map((part, i) => (
        <span key={i} className={cn(part.added && 'rounded-sm bg-success/20 text-foreground',
          part.removed && 'rounded-sm bg-destructive/15 text-muted-foreground line-through')}>{part.value}</span>
      ))}
    </span>
  )
}

function lineText(cast: Map<string, CastMember>, d?: NonNullable<Beat['dialogue']>[number]) {
  if (!d) return ''
  return `${d.voiceover ? 'VO' : nameOf(cast, d.character)}${d.delivery ? ` (${d.delivery})` : ''}: ${d.line}`
}

function beatKey(b?: Beat) {
  return b ? JSON.stringify([b.action, b.dialogue, b.camera, b.lighting_color, b.sound, b.start_sec, b.end_sec]) : ''
}

/** Side-by-side meaning, inline rendering: what changed from `base` to `cur`, scene by scene, beat by beat. */
export function EpisodeDiff({ base, cur, cast, onlyChanged }: {
  base: EpisodeData
  cur: EpisodeData
  cast: Map<string, CastMember>
  onlyChanged: boolean
}) {
  const ids = [...new Set([...base.scenes.map((s) => s.id), ...cur.scenes.map((s) => s.id)])]
  let changedTotal = 0
  const blocks = ids.map((id) => {
    const a = base.scenes.find((s) => s.id === id)
    const b = cur.scenes.find((s) => s.id === id)
    const n = Math.max(a?.beats.length ?? 0, b?.beats.length ?? 0)
    const rows = Array.from({ length: n }, (_, i) => {
      const x = a?.beats[i], y = b?.beats[i]
      const changed = beatKey(x) !== beatKey(y)
      if (changed) changedTotal += 1
      if (onlyChanged && !changed) return null
      const lines = Math.max(x?.dialogue?.length ?? 0, y?.dialogue?.length ?? 0)
      return (
        <div key={i} className={cn('grid gap-x-4 px-5 py-3 md:grid-cols-[92px_minmax(0,1fr)]', changed && 'bg-warning/5')}>
          <div className="font-mono text-xs text-muted-foreground tabular-nums">
            {fmtTime((y ?? x)!.start_sec)}
            {!x && <div className="font-sans text-success">mới</div>}
            {!y && <div className="font-sans text-destructive">đã bỏ</div>}
          </div>
          <div className="min-w-0 space-y-1.5 font-serif text-[15px] leading-relaxed">
            <p><Words a={x?.action} b={y?.action} /></p>
            {Array.from({ length: lines }, (_, j) => (
              <p key={j} className="border-l-2 border-primary/30 pl-3"><Words a={lineText(cast, x?.dialogue?.[j])} b={lineText(cast, y?.dialogue?.[j])} /></p>
            ))}
            {(x?.camera !== y?.camera || x?.lighting_color !== y?.lighting_color || x?.sound !== y?.sound) && (
              <p className="font-sans text-xs text-muted-foreground">
                Máy: <Words a={x?.camera} b={y?.camera} /> · Sáng: <Words a={x?.lighting_color} b={y?.lighting_color} /> · Tiếng: <Words a={x?.sound} b={y?.sound} />
              </p>
            )}
          </div>
        </div>
      )
    }).filter(Boolean)
    if (!rows.length && onlyChanged) return null
    return (
      <section key={id} className="overflow-hidden rounded-xl border bg-paper">
        <div className="flex flex-wrap items-center gap-2 border-b bg-muted/30 px-5 py-2.5 text-sm">
          <span className="rounded bg-foreground px-1.5 py-0.5 font-mono text-[11px] font-semibold text-background">{id}</span>
          <span className="font-semibold uppercase"><Words a={a?.heading ?? a?.location} b={b?.heading ?? b?.location} /></span>
          {!a && <span className="text-xs text-success">cảnh mới</span>}
          {!b && <span className="text-xs text-destructive">cảnh đã bỏ</span>}
        </div>
        <div className="divide-y">{rows}</div>
      </section>
    )
  })
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {changedTotal ? `${changedTotal} đoạn thay đổi.` : 'Hai phiên bản giống nhau.'}{' '}
        <span className="rounded-sm bg-success/20 px-1 text-foreground">chữ thêm</span>{' '}
        <span className="rounded-sm bg-destructive/15 px-1 line-through">chữ bỏ</span>
      </p>
      {(base.cliffhanger !== cur.cliffhanger) && (
        <div className="rounded-xl border bg-card p-4 font-serif text-[15px]">
          <div className="mb-1 font-sans text-xs font-semibold text-primary uppercase">Cliffhanger</div>
          <Words a={base.cliffhanger} b={cur.cliffhanger} />
        </div>
      )}
      {blocks}
    </div>
  )
}
