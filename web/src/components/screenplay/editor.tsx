import { Camera, Lightbulb, Plus, Trash2, Volume2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Beat, DialogueLine } from '@/lib/api'
import { fmtTime } from '@/lib/format'
import type { CastMember } from './cast'

function Field({ icon: Icon, value, onChange, placeholder }: {
  icon: React.ComponentType<{ className?: string }>
  value?: string
  onChange: (v: string) => void
  placeholder: string
}) {
  return (
    <label className="flex items-center gap-1.5">
      <Icon className="size-3 shrink-0 text-muted-foreground" />
      <Input value={value ?? ''} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="h-7 text-xs" />
    </label>
  )
}

/** Edit one beat in place: action, every dialogue line, and the technical columns. Timing stays fixed. */
export function BeatEditor({ beat, index, cast, onChange }: {
  beat: Beat
  index: number
  cast: Map<string, CastMember>
  onChange: (b: Beat) => void
}) {
  const lines = beat.dialogue ?? []
  const setLine = (i: number, d: Partial<DialogueLine>) =>
    onChange({ ...beat, dialogue: lines.map((x, j) => (j === i ? { ...x, ...d } : x)) })
  const speakers = [...cast.values()]
  return (
    <div className="grid gap-x-4 gap-y-3 bg-primary/[0.03] px-4 py-3 sm:px-5 md:grid-cols-[92px_minmax(0,1fr)_220px]">
      <div className="text-xs text-muted-foreground">
        <div className="font-mono tabular-nums">{fmtTime(beat.start_sec)}</div>
        <div className="mt-0.5">#{index} · {beat.shot_size} · {(beat.end_sec - beat.start_sec).toFixed(1)}s</div>
      </div>
      <div className="min-w-0 space-y-2">
        <Textarea value={beat.action ?? ''} onChange={(e) => onChange({ ...beat, action: e.target.value })}
          placeholder="Hành động / hình ảnh" rows={2} className="bg-background font-serif text-[15px]" />
        {lines.map((d, i) => (
          <div key={i} className="rounded-md border bg-background p-2">
            <div className="flex flex-wrap items-center gap-2">
              <select value={d.character} onChange={(e) => setLine(i, { character: e.target.value })}
                className="h-7 rounded-md border bg-background px-2 text-xs">
                {speakers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                {!cast.has(d.character) && <option value={d.character}>{d.character}</option>}
              </select>
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={!!d.voiceover} onChange={(e) => setLine(i, { voiceover: e.target.checked })} /> VO
              </label>
              <Input value={d.delivery ?? ''} onChange={(e) => setLine(i, { delivery: e.target.value })} placeholder="cách nói" className="h-7 w-40 text-xs" />
              <button title="Xóa câu" className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted hover:text-destructive"
                onClick={() => onChange({ ...beat, dialogue: lines.filter((_, j) => j !== i) })}><Trash2 className="size-3.5" /></button>
            </div>
            <Textarea value={d.line} onChange={(e) => setLine(i, { line: e.target.value })} rows={1}
              className="mt-2 min-h-9 bg-background font-serif text-[15px]" />
          </div>
        ))}
        <button className="flex items-center gap-1 text-xs text-primary hover:underline"
          onClick={() => onChange({ ...beat, dialogue: [...lines, { character: speakers[0]?.id ?? 'char_01', line: '', voiceover: false, delivery: '' }] })}>
          <Plus className="size-3" /> Thêm câu thoại
        </button>
      </div>
      <div className="space-y-1.5">
        <Field icon={Camera} value={beat.camera} onChange={(v) => onChange({ ...beat, camera: v })} placeholder="máy quay" />
        <Field icon={Lightbulb} value={beat.lighting_color} onChange={(v) => onChange({ ...beat, lighting_color: v })} placeholder="ánh sáng / màu" />
        <Field icon={Volume2} value={beat.sound} onChange={(v) => onChange({ ...beat, sound: v })} placeholder="âm thanh" />
      </div>
    </div>
  )
}

/** Count changed beats between two episode JSONs (same structure: only text fields are editable). */
export function countChanges(a: { scenes: { beats: Beat[] }[] }, b: { scenes: { beats: Beat[] }[] }): number {
  let n = 0
  a.scenes.forEach((s, i) => s.beats.forEach((x, j) => {
    if (JSON.stringify(x) !== JSON.stringify(b.scenes[i]?.beats[j])) n += 1
  }))
  return n
}
