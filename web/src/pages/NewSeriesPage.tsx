import { useMutation, useQuery } from '@tanstack/react-query'
import { Check, FileUp, Palette, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { api, legacy, qk } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'

const DRAFT_KEY = 'story-dna-new-series'
const TEMPLATE = `Bối cảnh: (ở đâu, thời nào, có gì đặc biệt)

Nhân vật:
- (tên, tuổi): (là ai, muốn gì, giấu gì)
-

Cảnh muốn có:
-

Kết: (nếu đã nghĩ ra; chưa có cũng được)
`
const EP_SEC = [60, 75, 90, 120]
const STEPS = ['Phong cách', 'Ý tưởng', 'Độ dài & xác nhận']

interface Draft { slug: string; title: string; idea: string; episodes: number; episode_sec: number }

function loadDraft(): Partial<Draft> {
  try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || '{}') } catch { return {} }
}

export function NewSeriesPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const skills = useQuery({ queryKey: qk.skills, queryFn: api.skills })
  const [step, setStep] = useState(0)
  const [d, setD] = useState<Draft>(() => {
    const saved = loadDraft()
    return { slug: params.get('skill') || saved.slug || '', title: saved.title || '', idea: saved.idea || '',
      episodes: saved.episodes || 12, episode_sec: saved.episode_sec || 90 }
  })
  const fileRef = useRef<HTMLInputElement>(null)
  const set = (patch: Partial<Draft>) => setD((x) => ({ ...x, ...patch }))

  useEffect(() => {
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(d)) } catch { /* draft only lives in memory then */ }
  }, [d])
  useEffect(() => {
    if (!d.slug && skills.data?.length === 1) set({ slug: skills.data[0].slug })
  }, [skills.data, d.slug])

  const create = useMutation({
    mutationFn: () => api.createProject(d),
    onSuccess: (r) => {
      try { localStorage.removeItem(DRAFT_KEY) } catch { /* nothing to clear */ }
      askNotificationPermission()
      toast.success('Claude bắt đầu viết bible và outline. Xong sẽ có thông báo.')
      navigate(`/p/${r.slug}/${r.session_id}`)
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const skill = skills.data?.find((s) => s.slug === d.slug)
  const words = d.idea.trim() ? d.idea.trim().split(/\s+/).length : 0
  const canNext = [!!skill, d.idea.trim().length >= 20, true][step]
  const totalMin = Math.round((d.episodes * d.episode_sec) / 60)

  const readFile = (f: File) => {
    if (f.size > 500_000) { toast.error('File quá lớn (tối đa 500 KB chữ).'); return }
    f.text().then((t) => set({ idea: d.idea.trim() ? `${d.idea.trim()}\n\n${t}` : t }))
  }

  if (skills.data && !skills.data.length) {
    return (
      <main className="mx-auto max-w-xl px-4 py-16 text-center">
        <Palette className="mx-auto size-10 text-muted-foreground" />
        <h1 className="mt-4 text-xl font-semibold">Chưa có phong cách nào</h1>
        <p className="mt-2 text-muted-foreground">Học một video mẫu trước. Claude rút ra cách kể chuyện từ video đó, rồi bạn viết series theo phong cách ấy.</p>
        <Button render={<a href={legacy.analyzeNew} />} className="mt-6">Học video mẫu</Button>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">← Dự án</Link>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">Series mới</h1>
      <p className="mt-1 text-muted-foreground">Claude ghép ý tưởng của bạn vào khung truyện của phong cách, viết bible và outline, rồi dừng để bạn duyệt trước khi viết từng tập.</p>

      <ol className="mt-8 grid grid-cols-3 gap-2">
        {STEPS.map((label, i) => (
          <li key={label}>
            <button disabled={i > step && !canNext} onClick={() => i <= step && setStep(i)}
              className={cn('flex w-full items-center gap-2 border-t-[3px] pt-2 text-left text-sm',
                i < step ? 'border-success text-foreground' : i === step ? 'border-primary font-medium' : 'border-border text-muted-foreground')}>
              <span className={cn('flex size-5 items-center justify-center rounded-full text-[11px]',
                i < step ? 'bg-success text-white' : i === step ? 'bg-primary text-primary-foreground' : 'bg-muted')}>
                {i < step ? <Check className="size-3" /> : i + 1}
              </span>
              {label}
            </button>
          </li>
        ))}
      </ol>

      <div className="mt-6 rounded-xl border bg-card p-6">
        {step === 0 && (
          <div>
            <h2 className="font-semibold">Viết theo phong cách nào?</h2>
            <p className="mt-1 text-sm text-muted-foreground">Chỉ mượn cách kể (cấu trúc, nhịp, máy quay, âm thanh). Tên, nơi chốn, sự kiện của video mẫu không bị chép.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {skills.isLoading && [0, 1].map((i) => <Skeleton key={i} className="h-40" />)}
              {skills.data?.map((s) => (
                <button key={s.slug} onClick={() => set({ slug: s.slug })}
                  className={cn('rounded-xl border p-4 text-left transition', d.slug === s.slug ? 'border-primary bg-primary/5 ring-2 ring-primary/20' : 'hover:border-primary/40')}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold">{s.slug}</span>
                    {d.slug === s.slug ? <Check className="size-4 text-primary" /> : <span className="text-xs text-muted-foreground">{s.version}</span>}
                  </div>
                  <p className="mt-2 line-clamp-5 text-sm text-muted-foreground">{s.description}</p>
                  {s.reference && <p className="mt-2 text-xs text-muted-foreground">Học từ: {s.reference.title || s.reference.sources.join(', ')}</p>}
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_240px]">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Tên tạm của series <span className="font-normal text-muted-foreground">(không bắt buộc)</span></label>
                <Input value={d.title} onChange={(e) => set({ title: e.target.value })} placeholder="Ví dụ: Ngôi làng bão" className="mt-1.5" />
              </div>
              <div>
                <div className="flex items-end justify-between gap-2">
                  <label className="text-sm font-medium">Ý tưởng của bạn</label>
                  <div className="flex gap-1">
                    {!d.idea.trim() && <Button size="xs" variant="ghost" className="gap-1" onClick={() => set({ idea: TEMPLATE })}><Sparkles className="size-3" />Dùng mẫu</Button>}
                    <Button size="xs" variant="ghost" className="gap-1" onClick={() => fileRef.current?.click()}><FileUp className="size-3" />Tải file .md / .txt</Button>
                    <input ref={fileRef} type="file" accept=".md,.txt,text/plain,text/markdown" hidden
                      onChange={(e) => { const f = e.target.files?.[0]; if (f) readFile(f); e.target.value = '' }} />
                  </div>
                </div>
                <Textarea value={d.idea} onChange={(e) => set({ idea: e.target.value })} rows={16} className="mt-1.5 bg-background leading-relaxed"
                  placeholder={'Bối cảnh: làng chài miền Trung, mùa bão.\nNhân vật: Mai (17 tuổi, con gái người gác hải đăng), Tuấn (bạn thân), ông Bảy (trưởng làng).\nCảnh muốn có: Mai tìm thấy thư của mẹ trong căn phòng bị niêm phong.\nKết: chưa nghĩ ra, muốn có twist.'}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) readFile(f) }} />
                <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                  <span>Kéo thả file vào ô này cũng được. Bản nháp tự lưu trên trình duyệt.</span>
                  <span>{words} chữ</span>
                </div>
              </div>
            </div>
            <aside className="space-y-3 rounded-lg bg-muted/50 p-4 text-sm">
              <div className="font-medium">Viết thế nào?</div>
              <ul className="space-y-2 text-muted-foreground">
                <li>Rời rạc cũng được: vài nhân vật, một bối cảnh, vài cảnh bạn thích.</li>
                <li>Chỗ nào bỏ trống, Claude tự nghĩ theo phong cách và đánh dấu “[từ khung]”.</li>
                <li>Khi ý của bạn khác khung truyện, ý của bạn được ưu tiên.</li>
                <li>Viết bằng tiếng gì thì kịch bản ra tiếng đó.</li>
              </ul>
            </aside>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Số tập: <span className="text-primary">{d.episodes}</span></label>
                <input type="range" min={10} max={20} value={d.episodes} onChange={(e) => set({ episodes: Number(e.target.value) })} className="mt-3 w-full accent-[var(--primary)]" />
                <div className="flex justify-between text-xs text-muted-foreground"><span>10</span><span>20</span></div>
              </div>
              <div>
                <label className="text-sm font-medium">Độ dài mỗi tập</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {EP_SEC.map((s) => (
                    <button key={s} onClick={() => set({ episode_sec: s })}
                      className={cn('rounded-lg border px-3 py-1.5 text-sm', d.episode_sec === s ? 'border-primary bg-primary/5 font-medium text-primary' : 'hover:border-primary/40')}>
                      {s} giây
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="rounded-lg border bg-muted/30 p-4 text-sm">
              <div className="font-medium">Tóm tắt</div>
              <dl className="mt-2 grid grid-cols-[120px_minmax(0,1fr)] gap-y-1.5">
                <dt className="text-muted-foreground">Phong cách</dt><dd>{skill?.slug}</dd>
                <dt className="text-muted-foreground">Tên</dt><dd>{d.title || <span className="text-muted-foreground">(Claude đặt)</span>}</dd>
                <dt className="text-muted-foreground">Ý tưởng</dt><dd className="line-clamp-3 whitespace-pre-wrap">{d.idea.trim()}</dd>
                <dt className="text-muted-foreground">Thời lượng</dt><dd>{d.episodes} tập × {d.episode_sec} giây ≈ {totalMin} phút cả season</dd>
              </dl>
            </div>
            <div className="text-sm text-muted-foreground">
              <p><b className="text-foreground">Bước kế tiếp:</b> Claude viết bible + outline (khoảng 5–10 phút), rồi dừng để bạn đọc và duyệt.</p>
              <p className="mt-1">Duyệt xong mới viết {d.episodes} tập (khoảng {Math.round(d.episodes * 2)}–{d.episodes * 3} phút). Bạn có thể rời trang trong lúc chờ.</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Button variant="ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>Quay lại</Button>
        {step < 2 ? (
          <Button disabled={!canNext} onClick={() => setStep(step + 1)}>
            {step === 1 && d.idea.trim().length < 20 ? 'Viết thêm vài dòng' : 'Tiếp tục'}
          </Button>
        ) : (
          <Button disabled={create.isPending} onClick={() => create.mutate()} className="gap-1.5">
            <Sparkles className="size-4" /> Viết bible và outline
          </Button>
        )}
      </div>
    </main>
  )
}
