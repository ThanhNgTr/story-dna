import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

/** Long-form reading (bible, outline, adaptation): comfortable measure, wide tables scroll. */
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cn('prose prose-neutral max-w-none dark:prose-invert prose-headings:scroll-mt-20',
      'prose-table:text-sm prose-th:bg-muted/60 prose-td:align-top [&_table]:block [&_table]:overflow-x-auto', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
