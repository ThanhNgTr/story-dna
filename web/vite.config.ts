import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, type ProxyOptions } from 'vite'

const BACKEND = `http://127.0.0.1:${process.env.PORT || 8765}`

// API and reference images come from FastAPI (./run_app.sh). When it is not running, say so once
// per request in plain words instead of a stack trace.
const backend: ProxyOptions = {
  target: BACKEND,
  configure: (proxy) => {
    proxy.removeAllListeners('error') // Vite's own handler prints a stack trace per request
    proxy.on('error', (err, req, res) => {
      const msg = (err as NodeJS.ErrnoException).code === 'ECONNREFUSED'
        ? `Backend not running on ${BACKEND}: start it with ./run_app.sh (repo root).`
        : `Backend error: ${err.message}`
      console.warn(`[proxy] ${req.url} -> ${msg}`)
      if ('writeHead' in res && !res.headersSent) {
        res.writeHead(502, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ detail: msg }))
      }
    })
  },
}

// Build: served by FastAPI at /ui with assets under /static/ui/; the output is committed so people
// who run the app locally only need Python. Dev: Vite serves the app at http://127.0.0.1:5173/ui/.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/ui/' : '/',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
  build: { outDir: '../app/static/ui', emptyOutDir: true, chunkSizeWarningLimit: 900 },
  server: {
    port: 5173,
    proxy: { '/api': backend, '/series': backend },
  },
}))
