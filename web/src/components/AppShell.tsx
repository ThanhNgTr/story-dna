import { Clapperboard, Monitor, Moon, Plus, Sun } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router'
import { Button } from '@/components/ui/button'
import { useJobsStream } from '@/lib/events'
import { useTheme, type Theme } from '@/lib/theme'
import { cn } from '@/lib/utils'
import { JobCenter } from './JobCenter'

const NEXT: Record<Theme, Theme> = { system: 'light', light: 'dark', dark: 'system' }
const THEME_ICON = { system: Monitor, light: Sun, dark: Moon }
const THEME_LABEL = { system: 'Theo máy', light: 'Sáng', dark: 'Tối' }

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink to={to} end={to === '/'}
      className={({ isActive }) => cn('rounded-md px-3 py-1.5 text-sm transition-colors',
        isActive ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground hover:text-foreground')}>
      {children}
    </NavLink>
  )
}

export function AppShell() {
  useJobsStream()
  const [theme, setTheme] = useTheme()
  const Icon = THEME_ICON[theme]
  const onHome = useLocation().pathname === '/'
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-backdrop-filter:bg-background/70">
        <div className="mx-auto flex h-14 max-w-[1500px] items-center gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Clapperboard className="size-4" />
            </span>
            story-dna
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavItem to="/">Dự án</NavItem>
            <NavItem to="/videos/new">Học video mẫu</NavItem>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            {!onHome && <Button render={<NavLink to="/new" />} size="sm" className="mr-1 hidden gap-1 sm:inline-flex"><Plus className="size-3.5" />Series mới</Button>}
            <JobCenter />
            <Button variant="ghost" size="icon" title={`Giao diện: ${THEME_LABEL[theme]}`} onClick={() => setTheme(NEXT[theme])}>
              <Icon className="size-4" />
            </Button>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
