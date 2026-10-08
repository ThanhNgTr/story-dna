import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api, qk, type AssetKind, type Registry } from '@/lib/api'
import { askNotificationPermission } from '@/lib/events'

/** Registry + images of one series, and every action the looks pages can take. */
export function useLooks(slug: string, sid: string) {
  const qc = useQueryClient()
  const key = qk.assets(slug, sid)
  const query = useQuery({ queryKey: key, queryFn: () => api.assets(slug, sid) })
  const refresh = () => {
    qc.invalidateQueries({ queryKey: key })
    qc.invalidateQueries({ queryKey: ['project', slug, sid] })
  }
  const onError = (e: unknown) => toast.error((e as Error).message)
  const started = (msg: string) => () => {
    refresh()
    askNotificationPermission()
    toast.success(msg)
  }

  const generate = useMutation({
    mutationFn: (b: { kinds?: AssetKind[]; ids?: string[]; force?: boolean }) => api.generateImages(slug, sid, b),
    onSuccess: started('Codex bắt đầu tạo ảnh. Ảnh hiện dần khi xong từng tấm.'),
    onError,
  })
  const review = useMutation({
    mutationFn: ({ files, status }: { files: string[]; status: 'approved' | 'rejected' | 'draft' }) => api.reviewImages(slug, sid, files, status),
    onSuccess: refresh,
    onError,
  })
  const build = useMutation({
    mutationFn: (feedback: string) => api.buildAssets(slug, sid, feedback),
    onSuccess: started('Claude đang cập nhật kho ngoại hình (khoảng 5–10 phút).'),
    onError,
  })
  const save = useMutation({
    mutationFn: ({ data, note }: { data: Registry; note?: string }) =>
      api.saveAssets(slug, sid, query.data!.registry!.file, data, note),
    onSuccess: (r) => {
      refresh()
      toast.success(`Đã lưu thành ${r.file}`, { description: 'Mô tả mới chỉ vào ảnh khi bạn bấm “Tạo ảnh khác”.' })
    },
    onError,
  })
  return { ...query, generate, review, build, save }
}

export type Looks = ReturnType<typeof useLooks>
