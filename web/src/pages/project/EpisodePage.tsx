import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Clapperboard, Clock, Download, Sparkles, GitCompare, MessageSquare, PencilLine } from 'lucide-react'
import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { toast } from 'sonner'
import { AddCommentButton, CommentBubble, CommentComposer, CommentsPanel, useComments } from '@/components/screenplay/comments'
import { EpisodeDiff } from '@/components/screenplay/diff'
import { BeatEditor, countChanges } from '@/components/screenplay/editor'
import { BeatRow, CharacterChip, Cliffhanger, SceneHeader, SceneTimeline, type ReadMode, type SceneLook } from '@/components/screenplay/Screenplay'
import { approvedOf, thumb } from '@/components/looks/ImageTile'
import { useLooks } from '@/components/looks/useLooks'
import { castOf } from '@/components/screenplay/cast'
import { ConfirmAction } from '@/components/ConfirmAction'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { api, qk, type Beat, type Comment, type EpisodeData } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

const MODE_KEY = 'story-dna-read-mode'
type View = 'read' | 'edit' | 'compare'

function useReadMode() {
  const [mode, setMode] = useState<ReadMode>(() => {
    try { return localStorage.getItem(MODE_KEY) === 'full' ? 'full' : 'story' } catch { return 'story' }
  })
  const set = (m: ReadMode) => {
    setMode(m)
    try { localStorage.setItem(MODE_KEY, m) } catch { /* per-visit only */ }
  }
  return [mode, set] as const
}

interface LedgerQ { id: string; question: string }

function Ledger({ ep, questions }: { ep: EpisodeData; questions: Map<string, string> }) {
  const ledger = ep.ledger
  const evidence = (ep as { ledger_evidence?: Record<string, string> }).ledger_evidence
  if (!ledger) return null
  const groups: [string, unknown[] | undefined, string][] = [
    ['Mở ra', ledger.opened, 'text-info'], ['Manh mối', ledger.clues, 'text-warning'], ['Được trả lời', ledger.answered, 'text-success'],
  ]
  if (!groups.some(([, xs]) => xs?.length)) return null
  return (
    <div className="rounded-xl border bg-card p-5">
      <h3 className="font-semibold">Sổ bí ẩn của tập</h3>
      <div className="mt-3 space-y-3">
        {groups.map(([label, xs, color]) => xs?.length ? (
          <div key={label}>
            <div className={cn('text-xs font-semibold tracking-wide uppercase', color)}>{label}</div>
            <ul className="mt-1 space-y-1.5 text-sm">
              {xs.map((q) => {
                const id = String(q)
                return (
                  <li key={id}>
                    <span className="font-mono text-xs text-muted-foreground">{id}</span> {questions.get(id) ?? ''}
                    {evidence?.[id] && <div className="text-xs text-muted-foreground">↳ {evidence[id]}</div>}
                  </li>
                )
              })}
            </ul>
          </div>
        ) : null)}
      </div>
    </div>
  )
}

/** Text the user highlighted inside this beat, used as the comment's quote. */
function selectionIn(el: HTMLElement | null): string {
  const sel = window.getSelection()
  if (!el || !sel || sel.isCollapsed || !sel.anchorNode || !el.contains(sel.anchorNode)) return ''
  return sel.toString().trim().slice(0, 300)
}

function PolishEpisodeButton({ n, busy }: { n: number; busy: boolean }) {
  const p = useProject()
  const qc = useQueryClient()
  const run = useMutation({
    mutationFn: () => api.polishDialogue(p.slug, p.session_id, [n]),
    onSuccess: () => {
      toast.success(`Claude đang làm rõ thoại tập ${n}. Xong, bấm “So sánh phiên bản” để xem câu nào đổi.`)
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  return (
    <ConfirmAction trigger={<Button variant="outline" size="sm" className="gap-1.5" disabled={busy}><Sparkles className="size-3.5" /> Làm rõ thoại</Button>}
      title={`Làm rõ thoại tập ${n}?`} confirmLabel="Làm rõ" pending={run.isPending} onConfirm={() => run.mutateAsync()}
      description="Claude viết lại thoại và lời dẫn cho dễ hiểu, tự nhiên (theo quy tắc thoại tiếng Việt và cách bạn từng sửa tay). Chỉ đổi câu chữ; cảnh, thời lượng giữ nguyên. Kết quả là phiên bản mới, bản cũ vẫn giữ (khoảng 3–6 phút)." />
  )
}

function VideoPackageButton({ n, busy }: { n: number; busy: boolean }) {
  const p = useProject()
  const qc = useQueryClient()
  const ep = p.episodes.find((e) => e.n === n)
  const make = useMutation({
    mutationFn: () => api.makeShotlist(p.slug, p.session_id, [n]),
    onSuccess: () => {
      toast.success(`Claude đang tạo prompt video tập ${n} (khoảng 3–8 phút).`)
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })
  if (!ep) return null
  if (ep.has_prompts) {
    return (
      <Button variant="outline" size="sm" className="gap-1.5" render={<a href={api.packageUrl(p.slug, p.session_id, n)} download />}
        title="Gói zip cho Higgsfield: prompt từng shot, ảnh tham chiếu, phụ đề .srt, danh sách dựng .csv">
        <Download className="size-3.5" /> Tải gói video
      </Button>
    )
  }
  return (
    <Button variant="outline" size="sm" className="gap-1.5" disabled={busy || !ep.in_final || make.isPending}
      onClick={() => make.mutate()}
      title={!ep.in_final ? 'Chốt season trước: prompt video tạo từ bản cuối' : busy ? 'Đang có việc chạy cho series này'
        : 'Chia tập thành shot 1–5s và viết prompt video cho từng shot'}>
      <Clapperboard className="size-3.5" /> Tạo prompt video
    </Button>
  )
}

export function EpisodePage() {
  const p = useProject()
  const n = Number(useParams().n)
  const [params, setParams] = useSearchParams()
  const v = Number(params.get('v') || 0)
  const [mode, setMode] = useReadMode()
  const [view, setView] = useState<View>('read')
  const [activeScene, setActiveScene] = useState<string>()
  const [composing, setComposing] = useState<{ key: string; quote: string } | null>(null)
  const [draft, setDraft] = useState<EpisodeData | null>(null)
  const [note, setNote] = useState('')
  const [baseV, setBaseV] = useState(0)
  const [onlyChanged, setOnlyChanged] = useState(true)
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: qk.episode(p.slug, p.session_id, n, v),
    queryFn: () => api.episode(p.slug, p.session_id, n, v),
  })
  const latest = data ? data.versions.at(-1) ?? data.version : 0
  const compareV = baseV || (data && data.versions.length > 1 ? data.versions.at(-2)! : 0)
  const baseQ = useQuery({
    queryKey: qk.episode(p.slug, p.session_id, n, compareV),
    queryFn: () => api.episode(p.slug, p.session_id, n, compareV),
    enabled: view === 'compare' && compareV > 0,
  })
  const bible = useQuery({
    queryKey: qk.doc(p.slug, p.session_id, 'bible', 0),
    queryFn: () => api.doc(p.slug, p.session_id, 'bible'),
    enabled: p.docs.bible.length > 0,
  })
  const questions = useMemo(() => {
    const plan = (bible.data?.data as { ledger_plan?: LedgerQ[] } | null)?.ledger_plan ?? []
    return new Map(plan.map((q) => [q.id, q.question]))
  }, [bible.data])
  const hooks = useComments(p.slug, p.session_id)
  const byBeat = useMemo(() => {
    const m = new Map<string, Comment[]>()
    for (const c of hooks.comments) {
      if (c.episode !== n || c.status === 'resolved') continue
      const k = `${c.scene}#${c.beat}`
      m.set(k, [...(m.get(k) ?? []), c])
    }
    return m
  }, [hooks.comments, n])

  const save = useMutation({
    mutationFn: () => api.saveEpisode(p.slug, p.session_id, n, { base_version: latest, data: draft!, note }),
    onSuccess: (r) => {
      toast.success(`Đã lưu thành v${r.version}`, { description: r.lint && /lint: [1-9]\d* errors/.test(r.lint) ? 'Tập này chưa khớp kho ngoại hình (thiếu mã bối cảnh / trang phục). Xem mục Ngoại hình.' : undefined })
      setDraft(null); setNote(''); setView('read'); setParams({})
      qc.invalidateQueries({ queryKey: ['episode', p.slug, p.session_id, n] })
      qc.invalidateQueries({ queryKey: ['project', p.slug, p.session_id] })
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const dirty = draft && data ? countChanges(draft, data.data) : 0
  useEffect(() => {
    if (!dirty) return
    const warn = (e: BeforeUnloadEvent) => { e.preventDefault() }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  useEffect(() => { setView('read'); setDraft(null); setComposing(null); setBaseV(0) }, [n])

  const idx = p.episodes.findIndex((e) => e.n === n)
  const prev = p.episodes[idx - 1], next = p.episodes[idx + 1]
  const base = `/p/${p.slug}/${p.session_id}`
  const ep = view === 'edit' && draft ? draft : data?.data
  const looks = useLooks(p.slug, p.session_id)
  const reg = looks.data?.registry?.reg
  const cast = useMemo(() => {
    const m = data ? castOf(data.data as never) : new Map()
    for (const c of reg?.characters ?? []) {
      const img = approvedOf(c._img)
      if (img && m.has(c.char_id)) m.set(c.char_id, { ...m.get(c.char_id)!, photo: thumb(looks.data!.base, img.file, 160) })
    }
    return m
  }, [data, reg, looks.data])
  const sceneLooks = useMemo(() => {
    const out = new Map<string, SceneLook>()
    if (!reg || !data) return out
    const lb = `/p/${p.slug}/${p.session_id}/looks`
    for (const s of data.data.scenes) {
      const row = reg.scene_map.find((m) => Number(m.episode) === n && m.scene === s.id)
      const locId = s.loc_id ?? row?.loc_id
      const variant = s.variant_id ?? row?.variant_id ?? undefined
      const loc = reg.locations.find((l) => l.loc_id === locId)
      const wear = s.cast ?? row?.characters ?? {}
      out.set(s.id, {
        location: loc ? { name: loc.name, href: `${lb}/locations#${variant ?? loc.loc_id}`, variant: loc.variants.find((v) => v.variant_id === variant)?.time_of_day } : undefined,
        outfits: Object.entries(wear).map(([cid, oid]) => {
          const c = reg.characters.find((x) => x.char_id === cid)
          const o = c?.wardrobe.find((w) => w.outfit_id === oid)
          return { charId: cid, label: `${c?.name ?? cid}: ${o?.name ?? oid.replace(`${cid}_`, '')}`, href: `${lb}/characters#${oid}` }
        }),
      })
    }
    return out
  }, [reg, data, n, p.slug, p.session_id])
  const busy = !!p.job

  const jump = (id: string) => {
    setActiveScene(id)
    document.getElementById(`scene-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const jumpComment = (c: Comment) => {
    const el = document.getElementById(`beat-${c.scene}-${c.beat}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el?.classList.add('ring-2', 'ring-primary/50')
    setTimeout(() => el?.classList.remove('ring-2', 'ring-primary/50'), 1600)
  }
  const startEdit = () => {
    if (!data) return
    if (v && v !== latest) { toast.info('Chỉ sửa được bản mới nhất.'); setParams({}); return }
    setDraft(structuredClone(data.data)); setView('edit'); setComposing(null)
  }
  const setBeat = (si: number, bi: number, b: Beat) => setDraft((d) => {
    if (!d) return d
    const scenes = d.scenes.map((s, i) => (i !== si ? s : { ...s, beats: s.beats.map((x, j) => (j === bi ? b : x)) }))
    return { ...d, scenes }
  })

  if (error) return <p className="text-destructive">{(error as Error).message}</p>
  if (isLoading || !data || !ep) return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-[60vh]" /></div>

  const openHere = hooks.comments.filter((c) => c.episode === n && c.status === 'open').length
  const panel = <CommentsPanel episode={n} all={hooks.comments} onJump={jumpComment} hooks={hooks} busy={busy} />
  let beatNo = 0

  return (
    <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="min-w-0 space-y-5">
        <header className="rounded-xl border bg-card p-5">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="font-semibold tracking-wider">TẬP {String(n).padStart(2, '0')}</span>
            {ep.total_duration_sec != null && <span className="flex items-center gap-1"><Clock className="size-3" />{ep.total_duration_sec}s</span>}
            {ep.aspect_ratio && <span>· {ep.aspect_ratio}</span>}
            <span>· v{data.version}{data.version !== latest && ` (bản mới nhất v${latest})`}</span>
            <span className="ml-auto flex items-center gap-1">
              {prev && <Link to={`${base}/ep/${prev.n}`} className="rounded-md p-1 hover:bg-muted" title={`Tập ${prev.n}`}><ChevronLeft className="size-4" /></Link>}
              {next && <Link to={`${base}/ep/${next.n}`} className="rounded-md p-1 hover:bg-muted" title={`Tập ${next.n}`}><ChevronRight className="size-4" /></Link>}
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{ep.title}</h1>
          {ep.logline && <p className="mt-2 max-w-3xl text-muted-foreground">{ep.logline}</p>}
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            {[...cast.values()].filter((c) => !c.offscreen).map((c) => <CharacterChip key={c.id} c={c} />)}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {view === 'read' && (
              <ToggleGroup value={[mode]} onValueChange={(val) => val[0] && setMode(val[0] as ReadMode)} variant="outline" size="sm">
                <ToggleGroupItem value="story">Đọc truyện</ToggleGroupItem>
                <ToggleGroupItem value="full">Đầy đủ kỹ thuật</ToggleGroupItem>
              </ToggleGroup>
            )}
            <div className="ml-auto flex flex-wrap items-center gap-2">
              {data.versions.length > 1 && view !== 'edit' && (
                <Button variant={view === 'compare' ? 'secondary' : 'outline'} size="sm" className="gap-1.5"
                  onClick={() => setView(view === 'compare' ? 'read' : 'compare')}>
                  <GitCompare className="size-3.5" /> {view === 'compare' ? 'Thoát so sánh' : 'So sánh phiên bản'}
                </Button>
              )}
              {view !== 'edit' && <PolishEpisodeButton n={n} busy={busy} />}
              {view !== 'edit' && <VideoPackageButton n={n} busy={busy} />}
              {view !== 'edit' ? (
                <Button variant="outline" size="sm" className="gap-1.5" disabled={busy} onClick={startEdit}
                  title={busy ? 'Đang có việc chạy cho series này' : 'Sửa chữ trực tiếp, lưu thành phiên bản mới'}>
                  <PencilLine className="size-3.5" /> Sửa trực tiếp
                </Button>
              ) : null}
              <Sheet>
                <SheetTrigger render={<Button variant="outline" size="sm" className="gap-1.5 2xl:hidden" />}>
                  <MessageSquare className="size-3.5" /> Góp ý{openHere ? ` (${openHere})` : ''}
                </SheetTrigger>
                <SheetContent className="w-full overflow-y-auto sm:max-w-md">
                  <SheetHeader><SheetTitle>Góp ý</SheetTitle></SheetHeader>
                  <div className="px-4 pb-6">{panel}</div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
          {data.versions.length > 1 && view === 'read' && (
            <div className="mt-3 flex items-center gap-1 text-sm">
              <span className="mr-1 text-muted-foreground">Xem bản</span>
              {data.versions.map((x) => (
                <button key={x} onClick={() => setParams(x === latest ? {} : { v: String(x) })}
                  className={cn('rounded-md px-2 py-0.5', x === data.version ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground hover:bg-muted')}>
                  v{x}
                </button>
              ))}
            </div>
          )}
        </header>

        {view === 'compare' ? (
          <>
            <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card px-4 py-2.5 text-sm">
              <span>So bản</span>
              <select value={compareV} onChange={(e) => setBaseV(Number(e.target.value))} className="h-8 rounded-md border bg-background px-2">
                {data.versions.filter((x) => x !== data.version).map((x) => <option key={x} value={x}>v{x}</option>)}
              </select>
              <span>với v{data.version}</span>
              <label className="ml-auto flex items-center gap-1.5 text-muted-foreground">
                <input type="checkbox" checked={onlyChanged} onChange={(e) => setOnlyChanged(e.target.checked)} /> Chỉ hiện đoạn thay đổi
              </label>
            </div>
            {baseQ.data ? <EpisodeDiff base={baseQ.data.data} cur={data.data} cast={cast} onlyChanged={onlyChanged} />
              : <Skeleton className="h-64" />}
          </>
        ) : (
          <>
            <div className="sticky top-14 z-20 -mx-1 bg-background/90 px-1 py-2 backdrop-blur">
              <SceneTimeline ep={ep} onJump={jump} active={activeScene} />
            </div>
            {ep.scenes.map((s, si) => (
              <section key={s.id} id={`scene-${s.id}`} className="scroll-mt-28 overflow-hidden rounded-xl border bg-paper">
                <SceneHeader scene={s} cast={cast} look={sceneLooks.get(s.id)} />
                <div className="divide-y">
                  {s.beats.map((b, bi) => {
                    beatNo += 1
                    const no = beatNo
                    const key = `${s.id}#${no}`
                    const notes = byBeat.get(key) ?? []
                    if (view === 'edit') {
                      return <BeatEditor key={bi} beat={b} index={no} cast={cast} onChange={(nb) => setBeat(si, bi, nb)} />
                    }
                    return (
                      <Fragment key={bi}>
                        <div id={`beat-${s.id}-${no}`} className="rounded-sm transition-shadow">
                          <BeatRow beat={b} index={no} cast={cast} mode={mode}
                            actions={<AddCommentButton count={notes.length} onClick={() =>
                              setComposing({ key, quote: selectionIn(document.getElementById(`beat-${s.id}-${no}`)) })} />} />
                        </div>
                        {notes.length > 0 && (
                          <div className="space-y-2 px-4 pb-3 sm:px-5 md:pl-[124px]">
                            {notes.map((c) => (
                              <CommentBubble key={c.id} c={c} onUpdate={(f) => hooks.update.mutate({ id: c.id, ...f })}
                                onDelete={() => hooks.remove.mutate(c.id)} />
                            ))}
                          </div>
                        )}
                        {composing?.key === key && (
                          <CommentComposer initialQuote={composing.quote} pending={hooks.add.isPending}
                            onCancel={() => setComposing(null)}
                            onSubmit={(text, quote) => hooks.add.mutate(
                              { episode: n, version: data.version, scene: s.id, beat: no, time: b.start_sec, quote, text },
                              { onSuccess: () => setComposing(null) })} />
                        )}
                      </Fragment>
                    )
                  })}
                </div>
              </section>
            ))}
            {view === 'edit' ? (
              <div className="rounded-xl border bg-card p-4">
                <label className="text-xs font-medium text-muted-foreground">Cliffhanger</label>
                <Input value={draft?.cliffhanger ?? ''} onChange={(e) => setDraft((d) => d && { ...d, cliffhanger: e.target.value })} className="mt-1" />
              </div>
            ) : <Cliffhanger text={ep.cliffhanger} type={ep.cliffhanger_type} />}
            <Ledger ep={ep} questions={questions} />
          </>
        )}

        <div className={cn('flex justify-between text-sm', view === 'edit' ? 'pb-28' : 'pb-10')}>
          {prev ? <Link to={`${base}/ep/${prev.n}`} className="text-primary hover:underline">← Tập {prev.n}: {prev.title}</Link> : <span />}
          {next && <Link to={`${base}/ep/${next.n}`} className="text-primary hover:underline">Tập {next.n}: {next.title} →</Link>}
        </div>
      </div>

      <aside className="hidden 2xl:block">
        <div className="sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto rounded-xl border bg-card p-4">{panel}</div>
      </aside>

      {view === 'edit' && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 backdrop-blur">
          <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-3 px-4 py-3">
            <span className="text-sm font-medium">Đang sửa tập {n}</span>
            <span className="text-sm text-muted-foreground">{dirty ? `${dirty} đoạn đã đổi` : 'Chưa đổi gì'}</span>
            <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú cho lần sửa (không bắt buộc)" className="h-8 max-w-sm flex-1" />
            <div className="ml-auto flex gap-2">
              <Button variant="ghost" onClick={() => {
                if (dirty && !window.confirm('Bỏ các thay đổi chưa lưu?')) return
                setDraft(null); setView('read')
              }}>Hủy</Button>
              <Button disabled={!dirty || save.isPending} onClick={() => save.mutate()}>Lưu thành v{latest + 1}</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
