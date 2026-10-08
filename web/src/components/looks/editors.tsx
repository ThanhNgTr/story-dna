import { Pencil } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import type { RegCharacter, RegLocation, RegProp, Registry } from '@/lib/api'
import type { Looks } from './useLooks'

const FACE: [string, string][] = [['shape', 'Khuôn mặt'], ['eyes', 'Mắt'], ['brows', 'Lông mày'], ['nose', 'Mũi'], ['mouth', 'Miệng'], ['skin', 'Da'], ['marks', 'Dấu hiệu riêng']]
const BODY: [string, string][] = [['height', 'Chiều cao'], ['build', 'Vóc dáng'], ['posture', 'Dáng đứng / đi']]

function F({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      {hint && <span className="block text-xs text-muted-foreground">{hint}</span>}
      <div className="mt-1">{children}</div>
    </label>
  )
}

const lines = (xs?: string[]) => (xs ?? []).join('\n')
const unlines = (s: string) => s.split('\n').map((x) => x.trim()).filter(Boolean)

/** Shared shell: a side sheet with the form, a note and save -> new registry version (no Claude). */
function EditSheet<T>({ title, initial, looks, render, apply }: {
  title: string
  initial: T
  looks: Looks
  render: (v: T, set: (patch: Partial<T>) => void) => React.ReactNode
  apply: (reg: Registry, v: T) => Registry
}) {
  const [open, setOpen] = useState(false)
  const [v, setV] = useState<T>(initial)
  const [note, setNote] = useState('')
  const reg = looks.data?.registry?.reg
  return (
    <Sheet open={open} onOpenChange={(o) => { setOpen(o); if (o) { setV(structuredClone(initial)); setNote('') } }}>
      <SheetTrigger render={<Button size="xs" variant="ghost" className="gap-1" />}><Pencil className="size-3" /> Sửa</SheetTrigger>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
          <SheetDescription>Lưu thành phiên bản kho mới (bản cũ giữ nguyên). Ảnh không tự đổi: bấm “Tạo ảnh khác” sau khi lưu.</SheetDescription>
        </SheetHeader>
        <div className="space-y-4 px-4">{render(v, (patch) => setV((x) => ({ ...x, ...patch })))}</div>
        <SheetFooter className="gap-2">
          <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú (không bắt buộc)" />
          <Button disabled={!reg || looks.save.isPending}
            onClick={() => looks.save.mutate({ data: apply(structuredClone(reg!), v), note }, { onSuccess: () => setOpen(false) })}>
            Lưu thành phiên bản mới
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

export function EditCharacter({ c, looks }: { c: RegCharacter; looks: Looks }) {
  const face = typeof c.face === 'object' && c.face ? c.face : {}
  const body = typeof c.body === 'object' && c.body ? c.body : {}
  const initial = { face: { ...face }, body: { ...body }, hair: c.hair ?? '', invariants: lines(c.invariants), prompt_en: c.prompt_en ?? '',
    wardrobe: c.wardrobe.map((o) => ({ outfit_id: o.outfit_id, name: o.name ?? '', desc: o.desc ?? '', when: o.when ?? '', prompt_en: o.prompt_en ?? '' })) }
  type V = typeof initial
  return (
    <EditSheet<V> title={`Sửa ${c.name}`} initial={initial} looks={looks}
      apply={(reg, v) => {
        const x = reg.characters.find((y) => y.char_id === c.char_id)!
        x.face = v.face; x.body = v.body; x.hair = v.hair; x.invariants = unlines(v.invariants); x.prompt_en = v.prompt_en
        for (const o of v.wardrobe) Object.assign(x.wardrobe.find((w) => w.outfit_id === o.outfit_id)!, o)
        return reg
      }}
      render={(v, set) => (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            {FACE.map(([k, label]) => (
              <F key={k} label={label}><Input value={v.face[k] ?? ''} onChange={(e) => set({ face: { ...v.face, [k]: e.target.value } })} /></F>
            ))}
            <F label="Tóc"><Input value={v.hair} onChange={(e) => set({ hair: e.target.value })} /></F>
            {BODY.map(([k, label]) => (
              <F key={k} label={label}><Input value={v.body[k] ?? ''} onChange={(e) => set({ body: { ...v.body, [k]: e.target.value } })} /></F>
            ))}
          </div>
          <F label="Không bao giờ đổi" hint="Mỗi dòng một điểm, giữ giống nhau ở mọi tập.">
            <Textarea rows={3} value={v.invariants} onChange={(e) => set({ invariants: e.target.value })} />
          </F>
          <F label="Mô tả cho máy tạo ảnh (tiếng Anh)" hint="Ảnh được tạo từ đoạn này. Chỉ tả người, không tả quần áo.">
            <Textarea rows={4} value={v.prompt_en} onChange={(e) => set({ prompt_en: e.target.value })} />
          </F>
          {v.wardrobe.map((o, i) => {
            const setO = (patch: Partial<typeof o>) => set({ wardrobe: v.wardrobe.map((w, j) => (j === i ? { ...w, ...patch } : w)) })
            return (
              <fieldset key={o.outfit_id} className="space-y-2 rounded-lg border p-3">
                <legend className="px-1 text-sm font-medium">Trang phục {o.outfit_id}</legend>
                <F label="Tên"><Input value={o.name} onChange={(e) => setO({ name: e.target.value })} /></F>
                <F label="Mô tả"><Textarea rows={2} value={o.desc} onChange={(e) => setO({ desc: e.target.value })} /></F>
                <F label="Khi nào mặc"><Input value={o.when} onChange={(e) => setO({ when: e.target.value })} /></F>
                <F label="Mô tả cho máy tạo ảnh (tiếng Anh)"><Textarea rows={2} value={o.prompt_en} onChange={(e) => setO({ prompt_en: e.target.value })} /></F>
              </fieldset>
            )
          })}
        </>
      )} />
  )
}

export function EditLocation({ l, looks }: { l: RegLocation; looks: Looks }) {
  const initial = { name: l.name, desc: l.desc ?? '', layout: l.layout ?? '', fixed: lines(l.fixed_elements), prompt_en: l.prompt_en ?? '',
    variants: l.variants.map((x) => ({ variant_id: x.variant_id, lighting: x.lighting ?? '', prompt_en: x.prompt_en ?? '' })) }
  type V = typeof initial
  return (
    <EditSheet<V> title={`Sửa ${l.name}`} initial={initial} looks={looks}
      apply={(reg, v) => {
        const x = reg.locations.find((y) => y.loc_id === l.loc_id)!
        x.name = v.name; x.desc = v.desc; x.layout = v.layout; x.fixed_elements = unlines(v.fixed); x.prompt_en = v.prompt_en
        for (const nv of v.variants) Object.assign(x.variants.find((w) => w.variant_id === nv.variant_id)!, nv)
        return reg
      }}
      render={(v, set) => (
        <>
          <F label="Tên bối cảnh" hint="Kịch bản mới sẽ dùng đúng tên này."><Input value={v.name} onChange={(e) => set({ name: e.target.value })} /></F>
          <F label="Mô tả"><Textarea rows={3} value={v.desc} onChange={(e) => set({ desc: e.target.value })} /></F>
          <F label="Bố trí"><Textarea rows={3} value={v.layout} onChange={(e) => set({ layout: e.target.value })} /></F>
          <F label="Luôn có trong khung hình" hint="Mỗi dòng một thứ."><Textarea rows={4} value={v.fixed} onChange={(e) => set({ fixed: e.target.value })} /></F>
          <F label="Mô tả cho máy tạo ảnh (tiếng Anh)"><Textarea rows={4} value={v.prompt_en} onChange={(e) => set({ prompt_en: e.target.value })} /></F>
          {v.variants.map((x, i) => (
            <fieldset key={x.variant_id} className="space-y-2 rounded-lg border p-3">
              <legend className="px-1 text-sm font-medium">{x.variant_id}</legend>
              <F label="Ánh sáng / màu"><Input value={x.lighting} onChange={(e) => set({ variants: v.variants.map((w, j) => (j === i ? { ...w, lighting: e.target.value } : w)) })} /></F>
              <F label="Thời điểm + ánh sáng (tiếng Anh)"><Input value={x.prompt_en} onChange={(e) => set({ variants: v.variants.map((w, j) => (j === i ? { ...w, prompt_en: e.target.value } : w)) })} /></F>
            </fieldset>
          ))}
        </>
      )} />
  )
}

export function EditProp({ p, looks }: { p: RegProp; looks: Looks }) {
  const initial = { name: p.name, desc: p.desc ?? '', prompt_en: p.prompt_en ?? '' }
  type V = typeof initial
  return (
    <EditSheet<V> title={`Sửa ${p.name}`} initial={initial} looks={looks}
      apply={(reg, v) => { Object.assign(reg.props.find((y) => y.prop_id === p.prop_id)!, v); return reg }}
      render={(v, set) => (
        <>
          <F label="Tên"><Input value={v.name} onChange={(e) => set({ name: e.target.value })} /></F>
          <F label="Mô tả" hint="Chữ trên đồ vật ghi đúng nguyên văn."><Textarea rows={3} value={v.desc} onChange={(e) => set({ desc: e.target.value })} /></F>
          <F label="Mô tả cho máy tạo ảnh (tiếng Anh)"><Textarea rows={3} value={v.prompt_en} onChange={(e) => set({ prompt_en: e.target.value })} /></F>
        </>
      )} />
  )
}
