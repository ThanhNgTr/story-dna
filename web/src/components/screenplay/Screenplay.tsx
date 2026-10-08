import { Camera, Clapperboard, Lightbulb, MapPin, Volume2 } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { Beat, EpisodeData, Scene } from '@/lib/api'
import { fmtTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import { SHOT_LABEL, hueOf, nameOf, type CastMember } from './cast'

export type ReadMode = 'story' | 'full'

/** Long takes are a style device in these skills (one held 10-13s take per episode). */
const HELD_SEC = 8

export function CharacterChip({ c, small }: { c: CastMember; small?: boolean }) {
  const hue = hueOf(c.id)
  const chip = (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border bg-card', small ? 'py-0 pr-2 pl-0.5 text-xs' : 'py-0.5 pr-2.5 pl-1 text-sm')}>
      <span className={cn('flex items-center justify-center rounded-full font-semibold text-white', small ? 'size-4 text-[9px]' : 'size-6 text-[11px]')}
        style={{ background: `oklch(0.6 0.13 ${hue})` }}>
        {c.name.slice(0, 1).toUpperCase()}
      </span>
      {c.name}
    </span>
  )
  if (!c.look) return chip
  return (
    <Tooltip>
      <TooltipTrigger render={<span className="cursor-help" />}>{chip}</TooltipTrigger>
      <TooltipContent className="max-w-xs">{c.look}</TooltipContent>
    </Tooltip>
  )
}

export function SceneTimeline({ ep, onJump, active }: { ep: EpisodeData; onJump: (id: string) => void; active?: string }) {
  const total = ep.total_duration_sec || ep.scenes.at(-1)?.end_sec || 1
  return (
    <div className="flex h-9 w-full overflow-hidden rounded-lg border bg-muted/40">
      {ep.scenes.map((s, i) => {
        const w = ((s.end_sec - s.start_sec) / total) * 100
        return (
          <button key={s.id} onClick={() => onJump(s.id)} style={{ width: `${w}%` }}
            title={`${s.id} · ${fmtTime(s.start_sec)}–${fmtTime(s.end_sec)} · ${s.location ?? ''}`}
            className={cn('relative min-w-0 truncate border-r px-2 text-left text-xs transition-colors last:border-r-0',
              active === s.id ? 'bg-primary text-primary-foreground' : i % 2 ? 'bg-card hover:bg-accent' : 'bg-muted/60 hover:bg-accent')}>
            <span className="font-medium">{s.id}</span> <span className="opacity-70">{s.location}</span>
          </button>
        )
      })}
    </div>
  )
}

function Dialogue({ d, cast }: { d: NonNullable<Beat['dialogue']>[number]; cast: Map<string, CastMember> }) {
  const vo = !!d.voiceover
  return (
    <div className={cn('mt-2 rounded-md border-l-2 py-0.5 pl-3', vo ? 'border-vo/60' : 'border-primary/40')}>
      <div className="flex flex-wrap items-baseline gap-x-2 text-[11px] font-semibold tracking-wider uppercase">
        <span style={{ color: `oklch(0.55 0.13 ${hueOf(d.character)})` }}>{nameOf(cast, d.character)}</span>
        {vo && <span className="rounded bg-vo/15 px-1 text-[10px] text-vo">VO</span>}
        {d.delivery && <span className="font-normal tracking-normal text-muted-foreground normal-case italic">({d.delivery})</span>}
      </div>
      <p className={cn('font-serif text-[15px] leading-relaxed', vo && 'text-vo italic')}>{d.line}</p>
    </div>
  )
}

function Tech({ icon: Icon, children }: { icon: React.ComponentType<{ className?: string }>; children?: string }) {
  if (!children) return null
  return <div className="flex gap-1.5"><Icon className="mt-0.5 size-3 shrink-0 opacity-60" /><span>{children}</span></div>
}

export function BeatRow({ beat, index, cast, mode, actions }: {
  beat: Beat
  index: number
  cast: Map<string, CastMember>
  mode: ReadMode
  actions?: React.ReactNode
}) {
  const dur = beat.end_sec - beat.start_sec
  const held = dur >= HELD_SEC
  return (
    <div className={cn('group relative grid gap-x-4 gap-y-2 px-4 py-3 transition-colors hover:bg-muted/40 sm:px-5',
      mode === 'full' ? 'md:grid-cols-[92px_minmax(0,1fr)_220px]' : 'md:grid-cols-[92px_minmax(0,1fr)]',
      held && 'bg-warning/5')}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground md:block">
        <div className="font-mono tabular-nums">{fmtTime(beat.start_sec)}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-1">
          <span className="text-[10px] text-muted-foreground/70">#{index}</span>
          {beat.shot_size && (
            <span title={SHOT_LABEL[beat.shot_size] ?? beat.shot_size}
              className="rounded border px-1 font-mono text-[10px] font-medium text-foreground/80">{beat.shot_size}</span>
          )}
          <span className="tabular-nums">{dur.toFixed(1)}s</span>
        </div>
        {held && <div className="mt-1 text-[10px] font-semibold text-warning uppercase">Cú giữ dài</div>}
      </div>
      <div className="min-w-0">
        {beat.action && <p className="font-serif text-[15px] leading-relaxed">{beat.action}</p>}
        {beat.dialogue?.map((d, i) => <Dialogue key={i} d={d} cast={cast} />)}
      </div>
      {mode === 'full' && (
        <div className="space-y-1 text-xs text-muted-foreground">
          <Tech icon={Camera}>{beat.camera}</Tech>
          <Tech icon={Lightbulb}>{beat.lighting_color}</Tech>
          <Tech icon={Volume2}>{beat.sound}</Tech>
        </div>
      )}
      {actions && <div className="absolute top-2 right-2 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">{actions}</div>}
    </div>
  )
}

export function SceneHeader({ scene, cast }: { scene: Scene; cast: Map<string, CastMember> }) {
  const onScreen = scene.cast ? Object.keys(scene.cast)
    : [...new Set(scene.beats.flatMap((b) => b.characters ?? []))].filter((id) => cast.has(id) && !cast.get(id)?.offscreen)
  return (
    <div className="border-b bg-muted/30 px-4 py-3 sm:px-5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="rounded bg-foreground px-1.5 py-0.5 font-mono text-[11px] font-semibold text-background">{scene.id}</span>
        <h3 className="font-semibold tracking-wide uppercase">{scene.heading ?? `${scene.int_ext ?? ''}. ${scene.location ?? ''}`}</h3>
        <span className="ml-auto font-mono text-xs text-muted-foreground tabular-nums">{fmtTime(scene.start_sec)} – {fmtTime(scene.end_sec)}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        {scene.location && <span className="mr-1 inline-flex items-center gap-1"><MapPin className="size-3" />{scene.location}{scene.loc_id && <code className="ml-1 text-[10px]">{scene.loc_id}</code>}</span>}
        {onScreen.map((id) => cast.get(id) && <CharacterChip key={id} c={cast.get(id)!} small />)}
        {scene.cast && Object.entries(scene.cast).map(([id, o]) => (
          <code key={id} className="text-[10px]">{id}:{o.replace(`${id}_`, '')}</code>
        ))}
      </div>
    </div>
  )
}

export function Cliffhanger({ text, type }: { text?: string; type?: string }) {
  if (!text) return null
  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5">
      <div className="flex items-center gap-2 text-xs font-semibold tracking-wide text-primary uppercase">
        <Clapperboard className="size-4" /> Cliffhanger{type && <span className="font-normal normal-case">· {type}</span>}
      </div>
      <p className="mt-2 font-serif text-[15px] leading-relaxed">{text}</p>
    </div>
  )
}
