import { Navigate, Route, Routes } from 'react-router'
import { AppShell } from '@/components/AppShell'
import { JobPage } from '@/pages/JobPage'
import { HomePage } from '@/pages/HomePage'
import { NewSeriesPage } from '@/pages/NewSeriesPage'
import { DocPage } from '@/pages/project/DocPage'
import { EpisodePage } from '@/pages/project/EpisodePage'
import { HistoryPage } from '@/pages/project/HistoryPage'
import { LooksPage } from '@/pages/project/looks/LooksPage'
import { OverviewPage } from '@/pages/project/OverviewPage'
import { ProjectLayout } from '@/pages/project/ProjectLayout'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="new" element={<NewSeriesPage />} />
        <Route path="p/:slug/:sid" element={<ProjectLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="doc/:kind" element={<DocPage />} />
          <Route path="ep/:n" element={<EpisodePage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="looks" element={<Navigate to="characters" replace />} />
          <Route path="looks/:tab" element={<LooksPage />} />
        </Route>
        <Route path="jobs/:id" element={<JobPage />} />
        <Route path="*" element={<main className="p-10 text-muted-foreground">Không có trang này.</main>} />
      </Route>
    </Routes>
  )
}
