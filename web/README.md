# story-dna web UI

React + Vite + Tailwind + shadcn (Base UI). Built into `../app/static/ui/` and served by FastAPI at `/ui`.
See the "New UI" section of the root README for dev commands.

- `src/lib/api.ts`: typed client for `app/api.py`
- `src/lib/events.ts`: one SSE stream for job updates, toasts, notifications
- `src/pages/project/EpisodePage.tsx`: screenplay reader, comments, manual edit, version compare
- `scripts/e2e-episode.mjs`: browser test (system Chrome via playwright-core); run it on a COPY of a session
