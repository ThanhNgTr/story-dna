import { useMutation, useQuery } from '@tanstack/react-query'
import { HardDrive, History, Upload } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { LANGUAGES, api, qk, type ContinueBody } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'
import { Browser, ProbePanel, Uploader } from './videos/NewVideoPage'

type Mode = 'transcript' | 'none' | 'full'
type Source = 'disk' | 'upload' | 'run'
const EXTERNAL = 'external'
const SOURCES: { key: Source; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'disk', label: 'Trên máy này', icon: HardDrive },
  { key: 'upload', label: 'Tải lên', icon: Upload },
  { key: 'run', label: 'Bản phân tích đã có', icon: History },
]

function Card({ title, hint, children }: { title: string; hint?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border bg-card p-6">
      <h2 className="font-semibold">{title}</h2>
      {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
      <div className="mt-4">{children}</div>
    </section>
  )
}

function Choice({ checked, onSelect, title, badge, children, disabled }: {
  checked: boolean; onSelect: () => void; title: string; badge?: string; children: React.ReactNode; disabled?: boolean
}) {
  return (
    <label className={cn('flex cursor-pointer gap-3 rounded-lg border p-3 text-sm transition',
      checked ? 'border-primary/50 bg-primary/5' : 'hover:border-primary/30', disabled && 'pointer-events-none opacity-50')}>
      <input type="radio" className="mt-1 accent-primary" checked={checked} onChange={onSelect} disabled={disabled} />
      <span className="min-w-0">
        <span className="flex flex-wrap items-center gap-2 font-medium">{title}
          {badge && <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-normal text-muted-foreground">{badge}</span>}</span>
        <span className="mt-0.5 block text-muted-foreground">{children}</span>
      </span>
    </label>
  )
}

const selectCls = 'h-9 w-full rounded-md border bg-background px-2 text-sm'

export function ContinuePage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const projects = useQuery({ queryKey: qk.projects, queryFn: api.projects })
  const skills = useQuery({ queryKey: qk.skills, queryFn: api.skills })
  const analyses = useQuery({ queryKey: qk.analyses, queryFn: api.analyses })

  const initial = params.get('slug') && params.get('sid') ? `${params.get('slug')}/${params.get('sid')}` : ''
  const [target, setTarget] = useState(initial)
  const [styleSlug, setStyleSlug] = useState('')
  const [title, setTitle] = useState('')
  const [episodeSec, setEpisodeSec] = useState(90)
  const [mode, setMode] = useState<Mode>('transcript')
  const [source, setSource] = useState<Source>('disk')
  const [picked, setPicked] = useState('')
  const [runId, setRunId] = useState('')
  const [language, setLanguage] = useState('vi')
  const [produced, setProduced] = useState(1)
  const [newEps, setNewEps] = useState(6)
  const [direction, setDirection] = useState<'follow' | 'new-arc'>('follow')
  const [idea, setIdea] = useState('')
  const [notes, setNotes] = useState('')
  const [updateSkill, setUpdateSkill] = useState(false)

  const external = target === EXTERNAL
  const session = useMemo(() => projects.data?.find((p) => `${p.slug}/${p.session_id}` === target), [projects.data, target])
  const doneRuns = analyses.data?.filter((a) => a.done) ?? []

  // Defaults follow the chosen series: produced = episodes written so far, new = what the outline still plans
  useEffect(() => {
    if (!target && projects.data?.length) setTarget(`${projects.data[0].slug}/${projects.data[0].session_id}`)
  }, [projects.data, target])
  useEffect(() => {
    if (session) {
      const written = Math.max(session.episodes, session.produced, 1)
      const planned = session.planned ?? 0
      setProduced(written)
      setNewEps(planned > written ? planned - written : 6)
      setDirection('follow')
    } else if (external) {
      setDirection('new-arc')
      if (mode === 'none') setMode('transcript')
    }
  }, [session, external]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!styleSlug && skills.data?.length) setStyleSlug(skills.data[0].slug)
  }, [skills.data, styleSlug])

  const probe = useQuery({ queryKey: ['probe', picked], queryFn: () => api.probe(picked), enabled: !!picked && mode !== 'none' })
  const slug = external ? styleSlug : session?.slug ?? ''
  const sourceOk = mode === 'none' || (source === 'run' ? !!runId : !!picked && !!probe.data?.items.length)
  const ready = !!slug && (external || !!session) && sourceOk && produced >= 1 && newEps >= 1

  const start = useMutation({
    mutationFn: () => {
      const body: ContinueBody = {
        slug, sid: external ? '' : session!.session_id, title, episode_sec: episodeSec, canon_mode: mode,
        source: source === 'run' ? 'run' : 'videos', video_path: source === 'run' ? '' : picked, run_id: source === 'run' ? runId : '',
        language, produced_upto: produced, new_episodes: newEps, direction, idea, notes, update_skill: updateSkill && mode === 'full',
      }
      return api.continueSeries(body)
    },
    onSuccess: (r) => {
      askNotificationPermission()
      toast.success('Bắt đầu viết tiếp. Bạn có thể rời trang, xong sẽ có thông báo.')
      navigate(`/p/${r.slug}/${r.session_id}`)
    },
    onError: (e) => toast.error((e as Error).message),
  })

  if (projects.isLoading || skills.isLoading) return <main className="mx-auto max-w-4xl px-4 py-10"><Skeleton className="h-96" /></main>

  let step = 1
  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-10">
      <div>
        <Link to={session ? `/p/${session.slug}/${session.session_id}` : '/'} className="text-xs text-muted-foreground hover:text-foreground">
          ← {session ? session.title : 'Dự án'}
        </Link>
        <h1 className="mt-2 flex items-center gap-2 text-2xl font-semibold tracking-tight"><History className="size-6" /> Viết tiếp series</h1>
        <p className="mt-1 text-muted-foreground">
          Đã quay vài tập thành video? Claude học các tập đó, đối chiếu với kịch bản (cái đã lên hình được giữ), cập nhật bible và viết
          outline cho các tập tiếp theo. Sau đó dừng để bạn duyệt, chưa viết tập nào.
        </p>
      </div>

      <Card title={`${step++}. Series nào?`}>
        <select value={target} onChange={(e) => setTarget(e.target.value)} className={selectCls}>
          {projects.data?.map((p) => (
            <option key={`${p.slug}/${p.session_id}`} value={`${p.slug}/${p.session_id}`}>
              {p.title} — phong cách {p.slug}, {p.planned ?? '?'} tập ({p.session_id})
            </option>
          ))}
          <option value={EXTERNAL}>Series làm ngoài app (chưa có kịch bản trong app)</option>
        </select>
        {external && (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <label className="text-sm">Phong cách viết
              <select value={styleSlug} onChange={(e) => setStyleSlug(e.target.value)} className={cn(selectCls, 'mt-1')}>
                {skills.data?.map((s) => <option key={s.slug} value={s.slug}>{s.slug}{s.version ? ` (${s.version})` : ''}</option>)}
              </select>
            </label>
            <label className="text-sm">Tên series
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Ví dụ: Ngôi làng bão" className="mt-1" />
            </label>
            <label className="text-sm">Độ dài mỗi tập mới (giây)
              <Input type="number" min={60} max={120} value={episodeSec} onChange={(e) => setEpisodeSec(Number(e.target.value))} className="mt-1" />
            </label>
            <p className="text-xs text-muted-foreground sm:col-span-3">Claude tự dựng bible từ các video, rồi viết phần tiếp như một mạch truyện mới theo phong cách đã chọn.</p>
          </div>
        )}
      </Card>

      <Card title={`${step++}. Kiểm tra các tập đã quay thế nào?`}>
        <div className="space-y-2">
          <Choice checked={mode === 'transcript'} onSelect={() => setMode('transcript')} title="Nhanh: đối chiếu lời thoại" badge="~$1–2">
            {external ? 'Chép lời video trên máy (miễn phí), Claude dựng lại câu chuyện từ lời thoại. Không xem hình nên sẽ không biết ngoại hình nhân vật.'
              : 'Chép lời video trên máy (miễn phí), so từng câu với kịch bản: câu nào bị sửa, cắt, thêm. Claude chỉ đọc bản so sánh, không xem hình. Hợp khi quay sát kịch bản.'}
          </Choice>
          {!external && (
            <Choice checked={mode === 'none'} onSelect={() => setMode('none')} title="Bỏ qua: video quay đúng kịch bản" badge="~$1">
              Không xử lý video. Ghi chú những chỗ đã đổi khi quay (nếu có) ở ô bên dưới.
            </Choice>
          )}
          <Choice checked={mode === 'full'} onSelect={() => setMode('full')} title="Kỹ: xem cả hình" badge="~$0.45 / phút video">
            Claude xem khung hình từng đoạn như khi học video mẫu. Dùng khi hình ảnh đổi nhiều (diễn viên, bối cảnh, trang phục) hoặc muốn
            cập nhật phong cách từ video thật.
          </Choice>
        </div>
      </Card>

      {mode === 'none' ? (
        <Card title={`${step++}. Những chỗ đã đổi khi quay`} hint="Không bắt buộc.">
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="min-h-24"
            placeholder="Ví dụ: tập 3 bỏ cảnh hầm; tập 4 đổi tên Đạt thành Đức; diễn viên vai Linh tóc ngắn." />
        </Card>
      ) : (
        <Card title={`${step++}. Các tập đã làm thành video`} hint="Các tập được hiểu theo thứ tự tên file (Tập 1, Tập 2…). Chọn cả thư mục nếu có nhiều tập.">
          <div className="inline-flex flex-wrap rounded-lg border p-0.5">
            {SOURCES.filter((s) => s.key !== 'run' || doneRuns.length).map(({ key: k, label, icon: Icon }) => (
                <button key={k} onClick={() => setSource(k)}
                  className={cn('flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm', source === k ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground')}>
                  <Icon className="size-4" />{label}
                </button>
              ))}
          </div>
          <div className="mt-4">
            {source === 'disk' && <Browser picked={picked} onPick={setPicked} />}
            {source === 'upload' && <Uploader onDone={(path) => { setPicked(path); setSource('disk'); toast.success('Đã tải lên.') }} />}
            {source === 'run' && (
              <>
                <select value={runId} onChange={(e) => setRunId(e.target.value)} className={selectCls}>
                  <option value="">Chọn bản phân tích…</option>
                  {doneRuns.map((a) => <option key={a.id} value={a.id}>{a.title_vi || a.title || a.sources.join(', ')} — {a.sources.join(', ')} ({a.id})</option>)}
                </select>
                <p className="mt-1.5 text-xs text-muted-foreground">Dùng lại kết quả đã có, không tốn thêm thời gian xử lý video.</p>
              </>
            )}
          </div>
          {source !== 'run' && picked && <div className="mt-4">{probe.data ? <ProbePanel probe={probe.data} /> : <Skeleton className="h-20" />}</div>}
          {source !== 'run' && (
            <label className="mt-4 block max-w-xs text-sm">Ngôn ngữ thoại
              <select value={language} onChange={(e) => setLanguage(e.target.value)} className={cn(selectCls, 'mt-1')}>
                {LANGUAGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
          )}
        </Card>
      )}

      <Card title={`${step++}. Đã quay đến đâu, viết thêm bao nhiêu?`}>
        <div className="grid max-w-md grid-cols-2 gap-3">
          <label className="text-sm">Đã quay đến tập
            <Input type="number" min={1} max={100} value={produced} onChange={(e) => setProduced(Number(e.target.value))} className="mt-1" />
          </label>
          <label className="text-sm">Số tập mới cần viết
            <Input type="number" min={1} max={20} value={newEps} onChange={(e) => setNewEps(Number(e.target.value))} className="mt-1" />
          </label>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Tập 1 → {produced} đã có video. Claude viết outline cho tập {produced + 1} → {produced + newEps}; cả series vẫn phải có kết ở tập cuối.</p>
      </Card>

      {!external && (
        <Card title={`${step++}. Hướng đi của phần tiếp`}>
          <div className="space-y-2">
            <Choice checked={direction === 'follow'} onSelect={() => setDirection('follow')} title="Bám outline cũ">
              Giữ các tập còn lại của outline, chỉnh cho khớp những gì đã lên hình.
            </Choice>
            <Choice checked={direction === 'new-arc'} onSelect={() => setDirection('new-arc')} title="Mở một mạch truyện mới">
              Một phần mới sau các tập đã quay, với câu hỏi lớn mới.
            </Choice>
          </div>
        </Card>
      )}

      <Card title={`${step++}. Ý tưởng thêm cho phần tiếp`} hint="Không bắt buộc.">
        <Textarea value={idea} onChange={(e) => setIdea(e.target.value)} className="min-h-24"
          placeholder="Ví dụ: tập 8 cho Linh phát hiện ông Thụ là người gõ cửa; kết mùa ở ngày thứ mười." />
        <label className={cn('mt-4 flex items-start gap-2 text-sm', mode !== 'full' && 'opacity-50')}>
          <input type="checkbox" className="mt-1 accent-primary" checked={updateSkill && mode === 'full'} disabled={mode !== 'full'}
            onChange={(e) => setUpdateSkill(e.target.checked)} />
          <span>Cũng cập nhật phong cách <b>{slug || 'đã chọn'}</b> từ các video này (nhịp, góc quay, âm thanh thật), tạo phiên bản mới.
            <span className="block text-xs text-muted-foreground">Chỉ có ở mức Kỹ.</span></span>
        </label>
      </Card>

      <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
        <span className="text-xs text-muted-foreground">
          {mode === 'transcript' && 'Chép lời mất ~0.65× thời lượng video (trên máy). '}Đối chiếu + outline thêm 5–10 phút.
        </span>
        <Button size="lg" disabled={!ready || start.isPending} onClick={() => start.mutate()}>Đối chiếu & viết outline phần tiếp</Button>
      </div>
    </main>
  )
}
