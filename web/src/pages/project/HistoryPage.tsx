import { useProject } from './ProjectLayout'
import { fmtDate } from '@/lib/format'

export function HistoryPage() {
  const p = useProject()
  const rounds = [...p.iterations].reverse()
  return (
    <div className="rounded-xl border bg-card p-6">
      <h1 className="text-xl font-semibold">Lịch sử góp ý</h1>
      <p className="mt-1 text-sm text-muted-foreground">Mỗi vòng góp ý, duyệt hoặc cập nhật kho đều được ghi lại.</p>
      {rounds.length ? (
        <ol className="mt-6 space-y-6 border-l pl-6">
          {rounds.map((it) => (
            <li key={it.round} className="relative">
              <span className="absolute top-1.5 -left-[29px] size-2.5 rounded-full border-2 border-background bg-primary" />
              <div className="flex flex-wrap items-baseline gap-x-3 text-sm">
                <span className="font-semibold">Vòng {it.round}</span>
                <span className="text-muted-foreground">{fmtDate(it.timestamp)}</span>
                {it.stage && <span className="text-muted-foreground">· {it.stage}</span>}
                {it.skill_version_before && it.skill_version_after && it.skill_version_before !== it.skill_version_after &&
                  <span className="text-warning">· skill {it.skill_version_before} → {it.skill_version_after}</span>}
              </div>
              {it.feedback_raw && <blockquote className="mt-2 border-l-2 pl-3 text-sm italic">{it.feedback_raw}</blockquote>}
              {it.items?.length ? (
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {it.items.map((x, i) => <li key={i}>• {x.change ?? x.text}</li>)}
                </ul>
              ) : null}
              {it.files_written?.length ? (
                <div className="mt-2 text-xs text-muted-foreground">Tệp: {it.files_written.slice(0, 8).join(', ')}{it.files_written.length > 8 ? '…' : ''}</div>
              ) : null}
            </li>
          ))}
        </ol>
      ) : <p className="mt-6 text-sm text-muted-foreground">Chưa có vòng nào.</p>}
    </div>
  )
}
