import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, MessageSquarePlus, Pencil, Send, Trash2, Undo2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { api, qk, type Comment, type CommentDraft } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'
import { fmtDate, fmtTime } from '@/lib/format'
import { cn } from '@/lib/utils'

/** Quick starters: most notes on a 60-90s episode are one of these. */
const QUICK = ['Thoại cứng, chưa tự nhiên', 'Quá dài, cắt bớt', 'Thiếu cảm xúc', 'Chưa rõ ai làm gì', 'Lộ bí mật quá sớm', 'Không khớp tập trước']

export function useComments(slug: string, sid: string) {
  const qc = useQueryClient()
  const key = qk.comments(slug, sid)
  const query = useQuery({ queryKey: key, queryFn: () => api.comments(slug, sid) })
  const refresh = () => qc.invalidateQueries({ queryKey: key })
  const onError = (e: unknown) => toast.error((e as Error).message)
  const add = useMutation({ mutationFn: (c: CommentDraft) => api.addComment(slug, sid, c), onSuccess: refresh, onError })
  const update = useMutation({
    mutationFn: ({ id, ...f }: { id: string; text?: string; status?: 'open' | 'resolved' }) => api.updateComment(slug, sid, id, f),
    onSuccess: refresh, onError,
  })
  const remove = useMutation({ mutationFn: (id: string) => api.deleteComment(slug, sid, id), onSuccess: refresh, onError })
  const send = useMutation({
    mutationFn: (body: { ids?: string[]; general?: string }) => api.sendComments(slug, sid, body),
    onSuccess: () => {
      refresh()
      qc.invalidateQueries({ queryKey: ['project', slug, sid] })
      askNotificationPermission()
      toast.success('Đã gửi góp ý cho Claude. Kịch bản mới sẽ thành phiên bản kế tiếp.')
    },
    onError,
  })
  return { comments: query.data ?? [], add, update, remove, send }
}

export function CommentComposer({ initialQuote, onSubmit, onCancel, pending }: {
  initialQuote?: string
  onSubmit: (text: string, quote: string) => void
  onCancel: () => void
  pending?: boolean
}) {
  const [text, setText] = useState('')
  const [quote, setQuote] = useState(initialQuote ?? '')
  return (
    <div className="mx-4 mb-3 rounded-lg border border-primary/30 bg-card p-3 shadow-sm sm:mx-5 md:ml-[124px]">
      {quote && (
        <div className="mb-2 flex items-start gap-2 text-xs text-muted-foreground">
          <span className="line-clamp-2 flex-1 border-l-2 pl-2 italic">“{quote}”</span>
          <button className="hover:text-foreground" onClick={() => setQuote('')}>bỏ trích</button>
        </div>
      )}
      <Textarea autoFocus value={text} onChange={(e) => setText(e.target.value)} rows={2}
        placeholder="Cần sửa gì ở đoạn này?" className="min-h-16 bg-background"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && text.trim()) onSubmit(text, quote)
          if (e.key === 'Escape') onCancel()
        }} />
      <div className="mt-2 flex flex-wrap gap-1">
        {QUICK.map((q) => (
          <button key={q} onClick={() => setText((t) => (t ? `${t}; ${q.toLowerCase()}` : q))}
            className="rounded-full border px-2 py-0.5 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground">{q}</button>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-end gap-2">
        <span className="mr-auto text-[11px] text-muted-foreground">Ctrl+Enter để lưu</span>
        <Button variant="ghost" size="sm" onClick={onCancel}>Hủy</Button>
        <Button size="sm" disabled={!text.trim() || pending} onClick={() => onSubmit(text, quote)}>Lưu góp ý</Button>
      </div>
    </div>
  )
}

export function CommentBubble({ c, onUpdate, onDelete, compact }: {
  c: Comment
  onUpdate: (f: { text?: string; status?: 'open' | 'resolved' }) => void
  onDelete: () => void
  compact?: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(c.text)
  const tone = c.status === 'open' ? 'border-warning/40 bg-warning/5' : c.status === 'sent' ? 'border-info/30 bg-info/5' : 'border-border bg-muted/40 opacity-70'
  return (
    <div className={cn('rounded-lg border p-2.5 text-sm', tone)}>
      {!compact && c.quote && <div className="mb-1 line-clamp-2 border-l-2 pl-2 text-xs text-muted-foreground italic">“{c.quote}”</div>}
      {editing ? (
        <div className="space-y-2">
          <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} className="bg-background" />
          <div className="flex justify-end gap-1">
            <Button size="xs" variant="ghost" onClick={() => { setEditing(false); setText(c.text) }}>Hủy</Button>
            <Button size="xs" onClick={() => { onUpdate({ text }); setEditing(false) }}>Lưu</Button>
          </div>
        </div>
      ) : <p className="whitespace-pre-wrap">{c.text}</p>}
      <div className="mt-1.5 flex items-center gap-1 text-[11px] text-muted-foreground">
        <span>{c.status === 'open' ? 'Chưa gửi' : c.status === 'sent' ? 'Đã gửi cho Claude' : 'Đã xử lý'} · {fmtDate(c.created_at)}</span>
        {!editing && (
          <span className="ml-auto flex gap-0.5">
            {c.status === 'open' && <button title="Sửa" className="rounded p-1 hover:bg-muted" onClick={() => setEditing(true)}><Pencil className="size-3" /></button>}
            {c.status !== 'resolved'
              ? <button title="Đánh dấu đã xử lý" className="rounded p-1 hover:bg-muted" onClick={() => onUpdate({ status: 'resolved' })}><Check className="size-3" /></button>
              : <button title="Mở lại" className="rounded p-1 hover:bg-muted" onClick={() => onUpdate({ status: 'open' })}><Undo2 className="size-3" /></button>}
            <button title="Xóa" className="rounded p-1 hover:bg-muted hover:text-destructive" onClick={onDelete}><Trash2 className="size-3" /></button>
          </span>
        )}
      </div>
    </div>
  )
}

export function AddCommentButton({ onClick, count }: { onClick: () => void; count: number }) {
  return (
    <Button variant="outline" size="xs" className="gap-1 bg-card shadow-xs" onClick={onClick} title="Góp ý cho đoạn này">
      <MessageSquarePlus className="size-3.5" />{count ? count : 'Góp ý'}
    </Button>
  )
}

/** Right-hand panel: every open note of this episode, a general note, and one send button. */
export function CommentsPanel({ episode, all, onJump, hooks, busy }: {
  episode: number
  all: Comment[]
  onJump: (c: Comment) => void
  hooks: ReturnType<typeof useComments>
  busy: boolean
}) {
  const [general, setGeneral] = useState('')
  const open = all.filter((c) => c.status === 'open')
  const here = open.filter((c) => c.episode === episode)
  const elsewhere = open.length - here.length
  const sent = all.filter((c) => c.episode === episode && c.status !== 'open').slice(-6).reverse()
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold">Góp ý cho tập {episode}</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">Rê chuột vào một đoạn, bấm “Góp ý”. Gom đủ rồi gửi một lần.</p>
      </div>
      {here.length ? (
        <ul className="space-y-2">
          {here.map((c) => (
            <li key={c.id}>
              <button className="mb-1 font-mono text-[11px] text-primary hover:underline" onClick={() => onJump(c)}>
                {c.scene}{c.beat ? ` · #${c.beat}` : ''}{c.time != null ? ` · ${fmtTime(c.time)}` : ''}
              </button>
              <CommentBubble c={c} compact onUpdate={(f) => hooks.update.mutate({ id: c.id, ...f })} onDelete={() => hooks.remove.mutate(c.id)} />
            </li>
          ))}
        </ul>
      ) : <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">Chưa có góp ý nào cho tập này.</p>}
      <div>
        <label className="text-xs font-medium text-muted-foreground">Góp ý chung (không bắt buộc)</label>
        <Textarea value={general} onChange={(e) => setGeneral(e.target.value)} rows={3} className="mt-1 bg-background"
          placeholder="Ví dụ: cả tập hơi chậm ở giữa; giữ nguyên cliffhanger." />
      </div>
      <Button className="w-full gap-2" disabled={busy || (!open.length) || hooks.send.isPending}
        onClick={() => hooks.send.mutate({ general })}>
        <Send className="size-4" /> Gửi {open.length} góp ý cho Claude sửa
      </Button>
      <p className="text-xs text-muted-foreground">
        {busy ? 'Đang có việc chạy cho series này, gửi khi xong.' : <>Claude viết lại thành phiên bản mới, giữ bản cũ để so sánh.{elsewhere > 0 && ` Gồm cả ${elsewhere} góp ý ở tập khác.`} Khoảng 3–10 phút.</>}
      </p>
      {sent.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-xs text-muted-foreground">Đã gửi / đã xử lý ({sent.length})</summary>
          <div className="mt-2 space-y-2">
            {sent.map((c) => <CommentBubble key={c.id} c={c} compact onUpdate={(f) => hooks.update.mutate({ id: c.id, ...f })} onDelete={() => hooks.remove.mutate(c.id)} />)}
          </div>
        </details>
      )}
    </div>
  )
}
