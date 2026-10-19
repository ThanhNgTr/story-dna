import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowUp, Check, Film, Folder, FolderOpen, HardDrive, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError, LANGUAGES, api, uploadVideo, type ProbeResult } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { cn } from '@/lib/utils'

type Source = 'disk' | 'upload'
interface Existing { message: string; partial: boolean; existing: { id: string; title: string | null; sources: string[]; done: boolean }[] }

export function Browser({ picked, onPick }: { picked: string; onPick: (path: string) => void }) {
  const [path, setPath] = useState('')
  const { data, isLoading } = useQuery({ queryKey: ['browse', path], queryFn: () => api.browse(path) })
  if (isLoading || !data) return <Skeleton className="h-64" />
  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="flex items-center gap-2 border-b bg-muted/40 px-3 py-2 text-sm">
        <FolderOpen className="size-4 shrink-0 text-muted-foreground" />
        <span className="truncate font-mono text-xs">{data.cwd}</span>
        {data.parent && <Button size="xs" variant="ghost" className="ml-auto gap-1" onClick={() => setPath(data.parent!)}><ArrowUp className="size-3" />Lên</Button>}
      </div>
      <div className="max-h-80 divide-y overflow-y-auto">
        {data.n_videos > 1 && (
          <button onClick={() => onPick(data.cwd)}
            className={cn('flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-accent', picked === data.cwd && 'bg-primary/10')}>
            <StatusBadge tone="run">cả thư mục</StatusBadge>
            <span className="font-medium text-primary">Chọn cả {data.n_videos} video trong thư mục này (các tập của một series)</span>
            {picked === data.cwd && <Check className="ml-auto size-4 text-primary" />}
          </button>
        )}
        {data.entries.map((e) => e.dir ? (
          <button key={e.path} onClick={() => setPath(e.path)} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted">
            <Folder className="size-4 text-muted-foreground" /> {e.name}/
          </button>
        ) : (
          <button key={e.path} onClick={() => onPick(e.path)}
            className={cn('flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-accent', picked === e.path && 'bg-primary/10')}>
            <Film className="size-4 text-muted-foreground" /> <span className="truncate">{e.name}</span>
            <span className="ml-auto shrink-0 text-xs text-muted-foreground">{e.size_mb} MB</span>
            {picked === e.path && <Check className="size-4 text-primary" />}
          </button>
        ))}
        {!data.entries.length && <p className="px-3 py-6 text-center text-sm text-muted-foreground">Thư mục trống. Chép video vào {data.input_dir} hoặc dùng tab “Tải lên”.</p>}
      </div>
    </div>
  )
}

export function Uploader({ onDone }: { onDone: (path: string) => void }) {
  const [folder, setFolder] = useState('')
  const [files, setFiles] = useState<{ file: File; pct: number; done: boolean; error?: string }[]>([])
  const [over, setOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const busy = files.some((f) => !f.done && !f.error && f.pct > 0)
  const add = (list: FileList | null) => {
    const vids = [...(list ?? [])].filter((f) => /\.(mp4|mov|mkv|avi|webm)$/i.test(f.name))
    if (!vids.length) { toast.error('Chỉ nhận file video (.mp4, .mov, .mkv, .avi, .webm).'); return }
    setFiles((xs) => [...xs, ...vids.map((file) => ({ file, pct: 0, done: false }))])
  }
  const start = async () => {
    const name = folder.trim() || (files.length > 1 ? `upload-${new Date().toISOString().slice(0, 10)}` : '')
    let last = ''
    for (let i = 0; i < files.length; i++) {
      if (files[i].done) continue
      try {
        const r = await uploadVideo(files[i].file, name, (pct) => setFiles((xs) => xs.map((x, j) => (j === i ? { ...x, pct } : x))))
        setFiles((xs) => xs.map((x, j) => (j === i ? { ...x, pct: 100, done: true } : x)))
        last = files.length > 1 ? r.folder : r.path
      } catch (e) {
        setFiles((xs) => xs.map((x, j) => (j === i ? { ...x, error: (e as Error).message } : x)))
      }
    }
    if (last) onDone(last)
  }
  return (
    <div className="space-y-3">
      <div onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); add(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className={cn('flex cursor-pointer flex-col items-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition',
          over ? 'border-primary bg-primary/5' : 'hover:border-primary/40')}>
        <Upload className="size-8 text-muted-foreground" />
        <p className="mt-2 font-medium">Kéo thả video vào đây, hoặc bấm để chọn</p>
        <p className="text-sm text-muted-foreground">Nhiều file = nhiều tập của một series (đặt tên theo thứ tự: Tập 1, Tập 2…). Video được chép vào máy chạy app.</p>
        <input ref={inputRef} type="file" accept="video/*" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      </div>
      {files.length > 0 && (
        <>
          {files.length > 1 && (
            <label className="block text-sm">Tên thư mục cho series này
              <Input value={folder} onChange={(e) => setFolder(e.target.value)} placeholder="ví dụ: truong-noi-tru" className="mt-1 max-w-xs" />
            </label>
          )}
          <ul className="space-y-2">
            {files.map((f, i) => (
              <li key={i} className="rounded-md border p-2.5 text-sm">
                <div className="flex justify-between gap-2"><span className="truncate">{f.file.name}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">{Math.round(f.file.size / 1e6)} MB</span></div>
                {f.error ? <p className="mt-1 text-xs text-destructive">{f.error}</p>
                  : (f.pct > 0 || f.done) && <Progress value={f.pct} className="mt-1.5 h-1.5" />}
              </li>
            ))}
          </ul>
          <Button onClick={start} disabled={busy || files.every((f) => f.done)} className="gap-1.5"><Upload className="size-4" />
            {busy ? 'Đang tải lên…' : `Tải lên ${files.filter((f) => !f.done).length} video`}</Button>
        </>
      )}
    </div>
  )
}

export function ProbePanel({ probe }: { probe: ProbeResult }) {
  return (
    <div className="space-y-3 rounded-lg border bg-muted/30 p-4 text-sm">
      <div className="font-medium">{probe.items.length} video · tổng {probe.minutes} phút</div>
      {probe.is_dir && (
        <ol className="list-decimal space-y-0.5 pl-5 text-muted-foreground">
          {probe.items.map((v) => <li key={v.name}>{v.name}{v.duration_sec ? ` (${(v.duration_sec / 60).toFixed(1)} phút)` : ''}</li>)}
        </ol>
      )}
      {probe.estimate && (
        <p className="text-muted-foreground">
          Ước tính <b className="text-foreground">{probe.estimate.total}</b>: chép lời ~{probe.estimate.transcribe}, {probe.estimate.units} đoạn × Claude ~{probe.estimate.analysts}, gộp ~{probe.estimate.merge}. Có thể đóng tab, việc vẫn chạy nền.
        </p>
      )}
      {probe.existing.length > 0 && (
        <p className="text-warning">Đã từng học một phần hoặc toàn bộ: {probe.existing.map((x) => (
          <Link key={x.id} to={`/videos/${x.id}`} className="underline">{x.title || x.id}</Link>
        )).reduce<React.ReactNode[]>((acc, el, i) => (i ? [...acc, ', ', el] : [el]), [])}.</p>
      )}
    </div>
  )
}

export function NewVideoPage() {
  const navigate = useNavigate()
  const [source, setSource] = useState<Source>('disk')
  const [picked, setPicked] = useState('')
  const [language, setLanguage] = useState('vi')
  const [chunk, setChunk] = useState(120)
  const [frames, setFrames] = useState(40)
  const [conflict, setConflict] = useState<Existing | null>(null)
  const probe = useQuery({ queryKey: ['probe', picked], queryFn: () => api.probe(picked), enabled: !!picked })
  const start = useMutation({
    mutationFn: (force: boolean) => api.startAnalysis({ video_path: picked, language, chunk_sec: chunk, max_frames: frames, force }),
    onSuccess: (job) => {
      askNotificationPermission()
      toast.success('Bắt đầu học video. Bạn có thể rời trang, xong sẽ có thông báo.')
      navigate(`/jobs/${job.id}`)
    },
    onError: (e) => {
      if (e instanceof ApiError && e.status === 409 && e.data && typeof e.data === 'object') setConflict(e.data as Existing)
      else toast.error((e as Error).message)
    },
  })

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">← Dự án</Link>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">Học một video mẫu</h1>
      <p className="mt-1 text-muted-foreground">Một video dài (nhiều tập ghép liền) hoặc một thư mục các tập. Claude xem hình, nghe thoại và rút ra cốt truyện, nhân vật, cách kể, máy quay, âm thanh, màu.</p>

      <div className="mt-8 rounded-xl border bg-card p-6">
        <h2 className="font-semibold">1. Chọn video</h2>
        <div className="mt-3 inline-flex rounded-lg border p-0.5">
          {([['disk', 'Trên máy này', HardDrive], ['upload', 'Tải lên', Upload]] as const).map(([k, label, Icon]) => (
            <button key={k} onClick={() => setSource(k)}
              className={cn('flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm', source === k ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground')}>
              <Icon className="size-4" />{label}
            </button>
          ))}
        </div>
        <div className="mt-4">
          {source === 'disk' ? <Browser picked={picked} onPick={setPicked} />
            : <Uploader onDone={(path) => { setPicked(path); setSource('disk'); toast.success('Đã tải lên. Kiểm tra lại rồi bấm Bắt đầu học.') }} />}
        </div>
        {picked && <div className="mt-4">{probe.data ? <ProbePanel probe={probe.data} /> : <Skeleton className="h-20" />}</div>}
      </div>

      <div className="mt-4 rounded-xl border bg-card p-6">
        <h2 className="font-semibold">2. Ngôn ngữ thoại trong video</h2>
        <select value={language} onChange={(e) => setLanguage(e.target.value)} className="mt-3 h-9 w-full max-w-xs rounded-md border bg-background px-2 text-sm">
          {LANGUAGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <p className="mt-1.5 text-xs text-muted-foreground">Chọn đúng giúp chép lời chính xác hơn (tự nhận diện dễ sai nếu video mở đầu bằng nhạc).</p>
        <details className="mt-4 text-sm">
          <summary className="cursor-pointer text-muted-foreground">Tùy chọn nâng cao</summary>
          <div className="mt-3 grid max-w-md grid-cols-2 gap-3">
            <label>Độ dài mỗi đoạn (giây)<Input type="number" min={60} max={300} value={chunk} onChange={(e) => setChunk(Number(e.target.value))} className="mt-1" /></label>
            <label>Số khung hình tối đa / đoạn<Input type="number" min={10} max={80} value={frames} onChange={(e) => setFrames(Number(e.target.value))} className="mt-1" /></label>
          </div>
        </details>
      </div>

      <div className="mt-6 flex justify-end">
        <Button size="lg" disabled={!picked || !probe.data?.items.length || start.isPending} onClick={() => start.mutate(false)}>Bắt đầu học video</Button>
      </div>

      <Dialog open={!!conflict} onOpenChange={(o) => !o && setConflict(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{conflict?.partial ? 'Lần trước mới học một phần' : 'Đã học những video này rồi'}</DialogTitle>
            <DialogDescription>
              {conflict?.partial ? 'Nên học lại cả thư mục để Claude thấy toàn bộ mạch truyện. Học xong có thể cập nhật phong cách cũ.'
                : 'Nên mở kết quả cũ (và tạo phong cách từ đó). Học lại từ đầu sẽ chạy lại toàn bộ và tốn thời gian.'}
            </DialogDescription>
          </DialogHeader>
          <ul className="space-y-1 text-sm">
            {conflict?.existing.map((x) => (
              <li key={x.id}><Link to={`/videos/${x.id}`} className="text-primary hover:underline">{x.title || x.id}</Link>
                <span className="text-muted-foreground"> — {x.sources.join(', ')}{x.done ? '' : ' (chưa xong)'}</span></li>
            ))}
          </ul>
          <DialogFooter>
            {conflict?.existing[0] && <Button variant="outline" render={<Link to={`/videos/${conflict.existing[0].id}`} />}>Mở kết quả cũ</Button>}
            <Button variant={conflict?.partial ? 'default' : 'secondary'} onClick={() => { setConflict(null); start.mutate(true) }}>
              {conflict?.partial ? 'Học lại cả thư mục' : 'Vẫn học lại từ đầu'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  )
}
