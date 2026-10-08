import { AlertTriangle, Check, MapPin, RefreshCcw, Shirt, Sparkles, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useLocation, useParams } from 'react-router'
import { ConfirmAction } from '@/components/ConfirmAction'
import { StatusBadge } from '@/components/StatusBadge'
import { EditCharacter, EditLocation, EditProp } from '@/components/looks/editors'
import { GenerateDialog } from '@/components/looks/GenerateDialog'
import { IMG_STATUS, ImageSet, thumb } from '@/components/looks/ImageTile'
import { useLooks, type Looks } from '@/components/looks/useLooks'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import type { AssetImage, Registry } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useProject } from '../ProjectLayout'

const TABS = [['characters', 'Nhân vật & trang phục'], ['locations', 'Bối cảnh'], ['props', 'Đạo cụ'], ['review', 'Duyệt ảnh'], ['issues', 'Lỗi liên tục']] as const

function useHashScroll() {
  const { hash } = useLocation()
  useEffect(() => {
    if (!hash) return
    const t = setTimeout(() => document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
    return () => clearTimeout(t)
  }, [hash])
}

function Detail({ label, children }: { label: string; children: React.ReactNode }) {
  if (!children) return null
  return (
    <div className="grid grid-cols-[120px_minmax(0,1fr)] gap-2 py-1 text-sm">
      <dt className="text-muted-foreground">{label}</dt><dd>{children}</dd>
    </div>
  )
}

const joinObj = (x: unknown) => (x && typeof x === 'object' ? Object.values(x as Record<string, string>).filter(Boolean).join('; ') : (x as string))

function Characters({ reg, eps, base, looks, busy, codex }: { reg: Registry; eps: number[]; base: string; looks: Looks; busy: boolean; codex: boolean }) {
  return (
    <div className="space-y-6">
      {eps.length > 0 && (
        <div className="overflow-x-auto rounded-xl border bg-card p-4">
          <h3 className="mb-2 font-semibold">Ai mặc gì ở tập nào</h3>
          <table className="w-full text-sm">
            <thead><tr><th className="py-1 text-left font-medium text-muted-foreground">Nhân vật</th>
              {eps.map((e) => <th key={e} className="px-2 py-1 text-center font-medium text-muted-foreground">T{e}</th>)}</tr></thead>
            <tbody>
              {reg.characters.map((c) => (
                <tr key={c.char_id} className="border-t">
                  <td className="py-1.5"><a href={`#${c.char_id}`} className="text-primary hover:underline">{c.name}</a></td>
                  {c._matrix.map((cell, i) => <td key={i} className={cn('px-2 text-center', !cell && 'text-muted-foreground/40')}>{cell || '·'}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {reg.characters.map((c) => (
        <section key={c.char_id} id={c.char_id} className="scroll-mt-24 rounded-xl border bg-card p-5">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 className="text-lg font-semibold">{c.name}</h2>
            <span className="text-sm text-muted-foreground">{c.char_id} · {c.tier} · {c.age} tuổi{c.apparent_age ? ` (trông ${c.apparent_age})` : ''}</span>
            <span className="ml-auto"><EditCharacter c={c} looks={looks} /></span>
          </div>
          <div className="mt-4 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            <dl>
              <Detail label="Khuôn mặt">{joinObj(c.face)}</Detail>
              <Detail label="Tóc">{c.hair}</Detail>
              <Detail label="Dáng người">{joinObj(c.body)}</Detail>
              {c.invariants?.length ? <Detail label="Không đổi"><ul className="list-disc pl-4">{c.invariants.map((x) => <li key={x}>{x}</li>)}</ul></Detail> : null}
              {c.inferred?.length ? <Detail label="Tự suy ra"><span className="text-muted-foreground">{c.inferred.join(', ')}</span></Detail> : null}
            </dl>
            <div>
              <div className="mb-2 text-sm font-medium">Bảng nhân vật</div>
              <ImageSet id={c.char_id} kind="character" set={c._img} base={base} label={c.name} looks={looks} busy={busy} codex={codex} />
            </div>
          </div>
          <div className="mt-6 space-y-5 border-t pt-4">
            {c.wardrobe.map((o) => (
              <div key={o.outfit_id} id={o.outfit_id} className="grid scroll-mt-24 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
                <div>
                  <div className="flex items-center gap-2 font-medium"><Shirt className="size-4 text-muted-foreground" />
                    {o.outfit_id.replace(`${c.char_id}_`, '')}{o.name ? ` — ${o.name}` : ''}
                    {o._default && <StatusBadge tone="muted">mặc định</StatusBadge>}
                  </div>
                  <p className="mt-1 text-sm">{o.desc}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{o.when}{o.episodes?.length ? ` · tập ${o.episodes.join(', ')}` : ''}</p>
                </div>
                {o._default && !o._img.images.length
                  ? <p className="self-center text-sm text-muted-foreground">Trang phục mặc định đã có trong bảng nhân vật.</p>
                  : <ImageSet id={o.outfit_id} kind="outfit" set={o._img} base={base} label={`${c.name} — ${o.name ?? o.outfit_id}`} looks={looks} busy={busy} codex={codex}
                    empty={!c._img.images.length ? 'Cần bảng nhân vật trước' : undefined} />}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

function Locations({ reg, base, looks, busy, codex }: { reg: Registry; base: string; looks: Looks; busy: boolean; codex: boolean }) {
  const name = (id?: string | null) => reg.locations.find((l) => l.loc_id === id)?.name
  return (
    <div className="space-y-6">
      {reg.locations.map((l) => (
        <section key={l.loc_id} id={l.loc_id} className="scroll-mt-24 rounded-xl border bg-card p-5">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 className="flex items-center gap-2 text-lg font-semibold"><MapPin className="size-4 text-muted-foreground" />{l.name}</h2>
            <span className="text-sm text-muted-foreground">{l.loc_id}{l.bible_id ? ` · bible ${l.bible_id}` : ''} · {l.int_ext}{l.parent ? ` · nằm trong ${name(l.parent) ?? l.parent}` : ''}</span>
            <span className="ml-auto"><EditLocation l={l} looks={looks} /></span>
          </div>
          <p className="mt-2 text-sm">{l.desc}</p>
          <dl className="mt-2">
            <Detail label="Bố trí">{l.layout}</Detail>
            {l.fixed_elements?.length ? <Detail label="Luôn có">{l.fixed_elements.join('; ')}</Detail> : null}
            {l.aliases?.length ? <Detail label="Tên trong kịch bản"><span className="text-muted-foreground">{l.aliases.join(' · ')}</span></Detail> : null}
            {l._scenes.length ? <Detail label="Dùng ở cảnh"><span className="text-muted-foreground">{l._scenes.join(', ')}</span></Detail> : null}
          </dl>
          <div className="mt-4 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {l.variants.map((v, i) => (
              <div key={v.variant_id} id={v.variant_id} className="scroll-mt-24">
                <div className="text-sm font-medium">{v.time_of_day}</div>
                <p className="mb-2 line-clamp-2 text-xs text-muted-foreground" title={v.lighting}>{v.lighting}</p>
                <ImageSet id={v.variant_id} kind="location" set={v._img} base={base} label={`${l.name} — ${v.time_of_day}`} looks={looks}
                  busy={busy} codex={codex} aspect="portrait" empty={i > 0 && !l.variants[0]._img.images.length ? 'Tạo ảnh thời điểm đầu trước' : undefined} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

function Props({ reg, base, looks, busy, codex }: { reg: Registry; base: string; looks: Looks; busy: boolean; codex: boolean }) {
  const owner = (id?: string | null) => reg.characters.find((c) => c.char_id === id)?.name
  if (!reg.props.length) return <p className="text-sm text-muted-foreground">Kho chưa có đạo cụ.</p>
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {reg.props.map((p) => (
        <section key={p.prop_id} id={p.prop_id} className="scroll-mt-24 rounded-xl border bg-card p-4">
          <div className="flex items-start gap-2">
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold">{p.name}</h3>
              <div className="text-xs text-muted-foreground">{p.prop_id}{p.owner ? ` · của ${owner(p.owner) ?? p.owner}` : ''}{p.episodes?.length ? ` · tập ${p.episodes.join(', ')}` : ''}</div>
            </div>
            <EditProp p={p} looks={looks} />
          </div>
          <p className="mt-2 mb-3 text-sm">{p.desc}</p>
          <ImageSet id={p.prop_id} kind="prop" set={p._img} base={base} label={p.name} looks={looks} busy={busy} codex={codex} aspect="square" />
        </section>
      ))}
    </div>
  )
}

/** Every image waiting for a decision, in one grid with multi-select. */
function Review({ reg, base, looks }: { reg: Registry; base: string; looks: Looks }) {
  const items = useMemo(() => {
    const out: { label: string; anchor: string; tab: string; img: AssetImage }[] = []
    const push = (label: string, tab: string, anchor: string, imgs: AssetImage[]) =>
      imgs.filter((i) => i.status === 'draft').forEach((img) => out.push({ label, tab, anchor, img }))
    for (const c of reg.characters) {
      push(`${c.name} — bảng nhân vật`, 'characters', c.char_id, c._img.images)
      for (const o of c.wardrobe) push(`${c.name} — ${o.name ?? o.outfit_id}`, 'characters', o.outfit_id, o._img.images)
    }
    for (const l of reg.locations) for (const v of l.variants) push(`${l.name} — ${v.time_of_day}`, 'locations', v.variant_id, v._img.images)
    for (const p of reg.props) push(p.name, 'props', p.prop_id, p._img.images)
    return out
  }, [reg])
  const [sel, setSel] = useState<Set<string>>(new Set())
  const files = [...sel]
  const act = (status: 'approved' | 'rejected') => looks.review.mutate({ files, status }, { onSuccess: () => setSel(new Set()) })
  if (!items.length) return <p className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">Không có ảnh nào chờ duyệt.</p>
  return (
    <div className="space-y-4">
      <div className="sticky top-14 z-10 flex flex-wrap items-center gap-2 rounded-lg border bg-card/95 px-4 py-2.5 backdrop-blur">
        <span className="text-sm">{items.length} ảnh chờ duyệt · đã chọn {sel.size}</span>
        <Button size="xs" variant="ghost" onClick={() => setSel(sel.size === items.length ? new Set() : new Set(items.map((x) => x.img.file)))}>
          {sel.size === items.length ? 'Bỏ chọn' : 'Chọn tất cả'}
        </Button>
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="outline" className="gap-1" disabled={!sel.size} onClick={() => act('rejected')}><X className="size-3.5" />Bỏ {sel.size || ''}</Button>
          <Button size="sm" className="gap-1 bg-success text-white hover:bg-success/90" disabled={!sel.size} onClick={() => act('approved')}><Check className="size-3.5" />Duyệt {sel.size || ''}</Button>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">Duyệt một ảnh mới sẽ thay ảnh chuẩn cũ của cùng mục. Bấm tên để mở mục đó.</p>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3">
        {items.map(({ label, tab, anchor, img }) => {
          const on = sel.has(img.file)
          return (
            <figure key={img.file} className={cn('overflow-hidden rounded-lg border bg-card', on && 'ring-2 ring-primary')}>
              <button className="block aspect-[4/3] w-full bg-muted" onClick={() => setSel((s) => { const n = new Set(s); if (on) n.delete(img.file); else n.add(img.file); return n })}>
                <img loading="lazy" src={thumb(base, img.file)} alt={label} className="size-full object-cover" />
              </button>
              <figcaption className="flex items-center gap-2 px-2.5 py-2 text-xs">
                <input type="checkbox" checked={on} readOnly className="pointer-events-none" />
                <Link to={`../${tab}#${anchor}`} relative="path" className="truncate hover:underline">{label}</Link>
                <span className="ml-auto text-muted-foreground">{IMG_STATUS[img.status].label}</span>
              </figcaption>
            </figure>
          )
        })}
      </div>
    </div>
  )
}

function Issues({ reg, projectBase }: { reg: Registry; projectBase: string }) {
  const sev = { high: ['nặng', 'bad'], medium: ['vừa', 'warn'], low: ['nhẹ', 'muted'] } as const
  if (!reg.issues.length) return <p className="text-sm text-muted-foreground">Không có lỗi nào.</p>
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Claude tìm thấy khi lập kho. Để sửa: mở tập tương ứng, bấm “Góp ý” ở đúng đoạn và dán cách sửa.</p>
      {reg.issues.map((i, k) => {
        const ep = /ep(\d+)/.exec(i.where ?? '')?.[1]
        return (
          <div key={k} className="rounded-xl border bg-card p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <StatusBadge tone={sev[i.severity]?.[1] ?? 'muted'}><AlertTriangle className="size-3" />{sev[i.severity]?.[0] ?? i.severity}</StatusBadge>
              <span className="font-mono text-xs">{i.where}</span>
              {i.type && <span className="text-xs text-muted-foreground">{i.type}</span>}
              {ep && <Link to={`${projectBase}/ep/${Number(ep)}`} className="ml-auto text-xs text-primary hover:underline">Mở tập {Number(ep)} →</Link>}
            </div>
            <p className="mt-2 text-sm">{i.problem}</p>
            {i.fix && <p className="mt-1.5 text-sm text-muted-foreground"><b className="font-medium text-foreground">Cách sửa:</b> {i.fix}</p>}
          </div>
        )
      })}
    </div>
  )
}

function Toolbar({ looks, busy, file, pending, counts }: { looks: Looks; busy: boolean; file: string; pending: Record<string, number>; counts: Record<string, number> }) {
  const [fb, setFb] = useState('')
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground">{file} · {counts.approved ?? 0} ảnh đã duyệt · {counts.draft ?? 0} chờ duyệt</span>
      <div className="ml-auto flex flex-wrap gap-2">
        <ConfirmAction trigger={<Button size="sm" variant="outline" className="gap-1.5" disabled={busy}><Sparkles className="size-3.5" /> Nhờ Claude sửa</Button>}
          title="Nhờ Claude sửa ngoại hình"
          description={<>
            <span className="block">Viết điều cần đổi. Claude cập nhật kho thành phiên bản mới, giữ nguyên mã nhân vật / bối cảnh nên ảnh cũ không mất.</span>
            <Textarea value={fb} onChange={(e) => setFb(e.target.value)} rows={4} className="mt-3"
              placeholder="Ví dụ: áo của Linh màu đỏ; bếp là phòng riêng; Vũ để râu lún phún từ tập 6" />
          </>}
          confirmLabel="Gửi cho Claude" pending={looks.build.isPending}
          onConfirm={() => (fb.trim() ? looks.build.mutateAsync(fb).then(() => setFb('')) : undefined)} />
        <ConfirmAction trigger={<Button size="sm" variant="outline" className="gap-1.5" disabled={busy}><RefreshCcw className="size-3.5" /> Cập nhật từ các tập</Button>}
          title="Cập nhật kho từ các tập mới nhất?"
          description="Claude đọc lại các tập, gắn cảnh với bối cảnh/trang phục, thêm thứ mới và tìm lỗi liên tục. Khoảng 5–10 phút."
          confirmLabel="Cập nhật" pending={looks.build.isPending} onConfirm={() => looks.build.mutateAsync('')} />
        {looks.data?.codex && <GenerateDialog pending={pending} looks={looks} busy={busy} />}
      </div>
    </div>
  )
}

export function LooksPage() {
  const p = useProject()
  const { tab = 'characters' } = useParams()
  const looks = useLooks(p.slug, p.session_id)
  useHashScroll()
  const busy = !!p.job
  const base = `/p/${p.slug}/${p.session_id}`
  const vm = looks.data?.registry

  if (looks.isLoading) return <div className="space-y-4"><Skeleton className="h-12" /><Skeleton className="h-96" /></div>
  if (!vm) {
    return (
      <div className="flex flex-col items-center rounded-xl border border-dashed bg-card px-6 py-14 text-center">
        <Shirt className="size-10 text-muted-foreground" />
        <h1 className="mt-4 text-lg font-semibold">Chưa có kho nhân vật & bối cảnh</h1>
        <p className="mt-1 max-w-lg text-sm text-muted-foreground">
          Claude chốt khuôn mặt, trang phục từng tập, bối cảnh và đạo cụ từ bible{p.episodes.length ? ' và các tập đã viết' : ''},
          để các tập và ảnh/video luôn khớp nhau. Khoảng 5–10 phút.
        </p>
        <Button className="mt-6" disabled={busy || looks.build.isPending} onClick={() => looks.build.mutate('')}>Lập kho</Button>
      </div>
    )
  }
  const counts: Record<string, number> = {
    characters: vm.reg.characters.length, locations: vm.reg.locations.length, props: vm.reg.props.length,
    review: vm.counts.draft ?? 0, issues: vm.reg.issues.length,
  }
  const common = { reg: vm.reg, base: looks.data!.base, looks, busy, codex: looks.data!.codex }
  return (
    <div className="space-y-5">
      <div className="rounded-xl border bg-card p-4">
        <h1 className="text-xl font-semibold">Ngoại hình</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Một nguồn duy nhất cho khuôn mặt, trang phục, bối cảnh, đạo cụ. Ảnh đã duyệt được dùng làm tham chiếu khi tạo shot và video.</p>
        <div className="mt-4"><Toolbar looks={looks} busy={busy} file={vm.file} pending={vm.pending} counts={vm.counts} /></div>
        {!looks.data!.codex && <p className="mt-3 text-xs text-warning">Chưa tìm thấy Codex CLI nên chưa tạo ảnh được (cài extension ChatGPT/Codex trong VS Code hoặc đặt CODEX_BIN).</p>}
      </div>
      <nav className="flex flex-wrap gap-1 border-b">
        {TABS.map(([key, label]) => (
          <NavLink key={key} to={`${base}/looks/${key}`}
            className={({ isActive }) => cn('-mb-px border-b-2 px-3 py-2 text-sm', isActive ? 'border-primary font-medium text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground')}>
            {label} <span className="text-xs text-muted-foreground">{counts[key]}</span>
          </NavLink>
        ))}
      </nav>
      {tab === 'characters' && <Characters {...common} eps={vm.episodes} />}
      {tab === 'locations' && <Locations {...common} />}
      {tab === 'props' && <Props {...common} />}
      {tab === 'review' && <Review reg={vm.reg} base={looks.data!.base} looks={looks} />}
      {tab === 'issues' && <Issues reg={vm.reg} projectBase={base} />}
    </div>
  )
}
