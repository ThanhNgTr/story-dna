import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Built into the FastAPI app (served at /ui, assets under /static/ui/). The build output is
// committed so people who run the app locally only need Python; Node is for UI development.
export default defineConfig({
  base: '/static/ui/',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
  build: { outDir: '../app/static/ui', emptyOutDir: true, chunkSizeWarningLimit: 900 },
  server: {
    port: 5173,
    // `npm run dev` + ./run_app.sh: API, images and old pages come from FastAPI
    proxy: { '/api': 'http://127.0.0.1:8765', '/series': 'http://127.0.0.1:8765', '/static': 'http://127.0.0.1:8765' },
  },
})
