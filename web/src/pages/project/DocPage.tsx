import { useQuery } from '@tanstack/react-query'
import { useParams, useSearchParams } from 'react-router'
import { Markdown } from '@/components/Markdown'
import { Skeleton } from '@/components/ui/skeleton'
import { api, qk } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useProject } from './ProjectLayout'

const TITLE: Record<string, string> = {
  adaptation: 'Ghép ý tưởng', bible: 'Series bible', outline: 'Outline', canon: 'Đối chiếu video đã quay',
}

export function DocPage() {
  const p = useProject()
  const { kind = 'bible' } = useParams()
  const [params, setParams] = useSearchParams()
  const v = Number(params.get('v') || 0)
  const versions = p.docs[kind as keyof typeof p.docs] ?? []
  const { data, isLoading, error } = useQuery({
    queryKey: qk.doc(p.slug, p.session_id, kind, v),
    queryFn: () => api.doc(p.slug, p.session_id, kind, v),
  })
  const shown = data?.version || versions.at(-1)
  return (
    <article className="rounded-xl border bg-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b px-6 py-4">
        <h1 className="text-xl font-semibold">{TITLE[kind] ?? kind}</h1>
        {versions.length > 1 && (
          <div className="flex items-center gap-1 text-sm">
            <span className="mr-1 text-muted-foreground">Phiên bản</span>
            {versions.map((n) => (
              <button key={n} onClick={() => setParams(n === versions.at(-1) ? {} : { v: String(n) })}
                className={cn('rounded-md px-2 py-0.5', n === shown ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground hover:bg-muted')}>
                v{n}
              </button>
            ))}
          </div>
        )}
      </header>
      <div className="px-6 py-6">
        {isLoading && <div className="space-y-3"><Skeleton className="h-6 w-2/3" /><Skeleton className="h-40" /></div>}
        {error && <p className="text-destructive">{(error as Error).message}</p>}
        {data && <Markdown>{data.markdown}</Markdown>}
      </div>
    </article>
  )
}
