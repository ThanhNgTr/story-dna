import { cn } from '@/lib/utils'
import type { Tone } from '@/lib/api'

const TONE: Record<string, string> = {
  ok: 'border-success/40 bg-success/10 text-success',
  warn: 'border-warning/40 bg-warning/10 text-warning',
  bad: 'border-destructive/40 bg-destructive/10 text-destructive',
  run: 'border-primary/40 bg-primary/10 text-primary',
  muted: 'border-border bg-muted text-muted-foreground',
  '': 'border-border bg-muted text-muted-foreground',
}

export function StatusBadge({ tone, children, className, pulse }: {
  tone: Tone
  children: React.ReactNode
  className?: string
  pulse?: boolean
}) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap',
      TONE[tone] ?? TONE[''], className)}>
      {(pulse || tone === 'run') && <span className="size-1.5 animate-pulse rounded-full bg-current" />}
      {children}
    </span>
  )
}
