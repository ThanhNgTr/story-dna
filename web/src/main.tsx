import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import App from './App'
import './index.css'

// Dev server root (http://127.0.0.1:5173/) -> the app lives under /ui like in the built version
if (!window.location.pathname.startsWith('/ui')) window.history.replaceState(null, '', '/ui/')

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10_000, refetchOnWindowFocus: true, retry: 1 } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter basename="/ui">
          <App />
        </BrowserRouter>
        <Toaster position="bottom-right" richColors />
      </TooltipProvider>
    </QueryClientProvider>
  </StrictMode>,
)
