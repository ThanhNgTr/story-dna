import type { Job, Tone } from './api'

export function fmtDuration(sec: number | null | undefined): string {
  if (sec == null) return ''
  const s = Math.round(sec)
  if (s < 60) return `${s} giây`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m} phút ${s % 60 ? `${s % 60} giây` : ''}`.trim()
  return `${Math.floor(m / 60)} giờ ${m % 60} phút`
}

/** 75.4 -> "01:15.4" (screenplay timecodes are seconds from the start of the episode) */
export function fmtTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec - m * 60
  return `${String(m).padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export const JOB_STATUS: Record<Job['status'], { label: string; tone: Tone }> = {
  queued: { label: 'Đang chờ', tone: 'muted' },
  running: { label: 'Đang chạy', tone: 'run' },
  done: { label: 'Xong', tone: 'ok' },
  failed: { label: 'Lỗi', tone: 'bad' },
  interrupted: { label: 'Bị gián đoạn', tone: 'warn' },
  cancelled: { label: 'Đã hủy', tone: 'muted' },
}

export const STEP_LABEL: Record<string, string> = {
  extract: 'Dò cắt cảnh, chia đoạn, lấy khung hình',
  transcribe: 'Chép lời thoại (WhisperX)',
  units: 'Claude phân tích từng đoạn',
  merge: 'Gộp thành cốt truyện + DNA',
  review: 'Nhà phân tích phim: soát lỗi + vì sao video cuốn',
  skill: 'Tạo skill viết series',
  outline: 'Viết ghép ý tưởng, bible và outline',
  episodes: 'Viết các tập',
  feedback: 'Sửa theo góp ý',
  final: 'Chốt season',
  canon_source: 'Video đã làm (canon)',
  continue: 'Đối chiếu video + outline phần tiếp',
  diff: 'So lời thoại kịch bản với video',
  images: 'Tạo ảnh tham chiếu bằng Codex',
  assets: 'Lập / cập nhật kho nhân vật, bối cảnh',
}

export function jobProgress(job: Job): number | null {
  for (const s of Object.values(job.steps)) {
    if (s.status === 'running' && typeof s.total === 'number' && s.total > 0) {
      return Math.round((100 * (s.done ?? 0)) / s.total)
    }
  }
  return null
}
