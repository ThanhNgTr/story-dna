import { ImagePlus } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import type { AssetKind } from '@/lib/api'
import type { Looks } from './useLooks'

const KINDS: [AssetKind, string, string][] = [
  ['character', 'Bảng nhân vật', 'mặt cận + 3 góc toàn thân, trang phục mặc định'],
  ['outfit', 'Trang phục khác', 'cùng người, gửi kèm bảng nhân vật'],
  ['location', 'Bối cảnh', 'mỗi thời điểm (ngày, đêm…) một ảnh, cùng một căn phòng'],
  ['prop', 'Đạo cụ', 'vật quan trọng, chữ trên vật giữ nguyên'],
]
const MIN_PER_IMAGE = 2.5

export function GenerateDialog({ pending, looks, busy }: { pending: Record<string, number>; looks: Looks; busy: boolean }) {
  const [kinds, setKinds] = useState<AssetKind[]>(['character', 'outfit', 'location'])
  const [open, setOpen] = useState(false)
  const count = kinds.reduce((n, k) => n + (pending[k] ?? 0), 0)
  const total = KINDS.reduce((n, [k]) => n + (pending[k] ?? 0), 0)
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" className="gap-1.5" disabled={busy || !total} />}>
        <ImagePlus className="size-4" /> Tạo ảnh còn thiếu{total ? ` (${total})` : ''}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Tạo ảnh tham chiếu</DialogTitle>
          <DialogDescription>Codex tạo lần lượt từng ảnh bằng tài khoản ChatGPT của bạn. Chỉ tạo mục chưa có ảnh; ảnh mới ở trạng thái “Chờ duyệt”.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {KINDS.map(([k, label, hint]) => (
            <label key={k} className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 hover:bg-muted/40">
              <input type="checkbox" className="mt-1" checked={kinds.includes(k)} disabled={!pending[k]}
                onChange={(e) => setKinds(e.target.checked ? [...kinds, k] : kinds.filter((x) => x !== k))} />
              <span className="flex-1">
                <span className="font-medium">{label}</span> <span className="text-sm text-muted-foreground">— còn {pending[k] ?? 0} ảnh</span>
                <span className="block text-xs text-muted-foreground">{hint}</span>
              </span>
            </label>
          ))}
        </div>
        <p className="text-sm text-muted-foreground">
          {count ? <>Sẽ tạo <b className="text-foreground">{count} ảnh</b>, khoảng {Math.round(count * MIN_PER_IMAGE)} phút. Bạn có thể rời trang; ảnh hiện dần khi xong.</> : 'Chọn ít nhất một loại còn thiếu ảnh.'}
        </p>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Để sau</DialogClose>
          <Button disabled={!count || looks.generate.isPending}
            onClick={() => looks.generate.mutate({ kinds }, { onSuccess: () => setOpen(false) })}>Tạo {count} ảnh</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
