// Typed client for the FastAPI JSON API (app/api.py).

export type Tone = 'ok' | 'warn' | 'bad' | 'run' | 'muted' | ''

export interface Stage { label: string; tone: Tone }

export interface JobStep { status: string; at?: string; total?: number; done?: number; failed?: number; [k: string]: unknown }

export interface Job {
  id: string
  kind: string
  title: string
  status: 'queued' | 'running' | 'done' | 'failed' | 'interrupted' | 'cancelled'
  steps: Record<string, JobStep>
  error: string | null
  cost_usd: number
  created_at: string
  started_at: string | null
  finished_at: string | null
  elapsed_sec: number | null
  eta_sec: number | null
  slug: string | null
  session_id: string | null
  result: Record<string, unknown>
}

export interface JobDetail extends Job { log: string[]; last_reply: string | null }

export interface ProjectSummary {
  slug: string
  session_id: string
  title: string
  episodes: number
  planned: number | null
  final: boolean
  has_outline: boolean
  missing: number[]
  produced: number
  stage: Stage
  created_at?: string
  episode_sec?: number
}

export interface EpisodeInfo {
  n: number
  versions: number[]
  in_final: boolean
  title: string | null
  logline: string | null
  duration_sec: number | null
  cliffhanger_type: string | null
  produced: boolean
}

export interface Iteration {
  round: number
  timestamp?: string
  stage?: string
  status?: string
  feedback_raw?: string | null
  skill_version_before?: string
  skill_version_after?: string
  items?: { text?: string; scope?: string; target?: string; change?: string }[]
  files_written?: string[]
}

export interface Project {
  slug: string
  session_id: string
  title: string
  skill: { name: string; description: string; version: string | null }
  input: { episodes: number; episode_sec: number; language: string; created_at: string; status?: string }
  stage: Stage
  planned: number
  produced_upto: number
  missing: number[]
  outline_approved: boolean
  final_complete: boolean
  docs: Record<'adaptation' | 'bible' | 'outline' | 'canon', number[]>
  episodes: EpisodeInfo[]
  assets: { file: string; counts: Record<string, number>; issues: number } | null
  iterations: Iteration[]
  job: Job | null
}

export interface DocResponse { kind: string; file: string; version: number; markdown: string; data: unknown }

// ----- episode screenplay JSON (write-series-<slug> Output Format) -----

export interface DialogueLine { character: string; line: string; voiceover?: boolean; delivery?: string }

export interface Beat {
  start_sec: number
  end_sec: number
  shot_size?: string
  characters?: string[]
  action?: string
  dialogue?: DialogueLine[]
  camera?: string
  lighting_color?: string
  sound?: string
}

export interface Scene {
  id: string
  start_sec: number
  end_sec: number
  location?: string
  heading?: string
  int_ext?: string
  time_of_day?: string
  loc_id?: string | null
  variant_id?: string | null
  cast?: Record<string, string>
  referenced?: string[]
  props?: string[]
  beats: Beat[]
}

export interface EpisodeData {
  episode: number
  title?: string
  logline?: string
  story_beats?: unknown
  cliffhanger_type?: string
  total_duration_sec?: number
  aspect_ratio?: string
  language?: string
  characters?: Record<string, { name?: string; visual_signature?: string | null; offscreen?: boolean }>
  scenes: Scene[]
  cliffhanger?: string
  ledger?: { opened?: unknown[]; clues?: unknown[]; answered?: unknown[] }
}

export interface EpisodeResponse { n: number; file: string; version: number; versions: number[]; data: EpisodeData; markdown: string | null }

export interface Comment {
  id: string
  episode: number
  version: number
  scene: string | null
  beat: number | null
  time: number | null
  quote: string
  text: string
  status: 'open' | 'sent' | 'resolved'
  created_at: string
  sent_in_job?: string
}

export type CommentDraft = Pick<Comment, 'episode' | 'version' | 'scene' | 'beat' | 'time' | 'quote' | 'text'>

export interface SaveResult { version: number; file: string; lint: string | null }

export interface Skill {
  slug: string
  name: string
  description: string
  version: string | null
  run_id: string | null
  projects: number
  reference: { id: string; title: string | null; minutes: number; sources: string[] } | null
}

export interface Analysis {
  id: string
  sources: string[]
  minutes: number
  language: string | null
  units: number
  analyzed: number
  done: boolean
  title: string | null
  logline: string | null
  genre: string | null
  skills: string[]
  job: Job | null
}

// ----- looks: asset registry (/series-assets) + reference images -----

export interface AssetImage {
  file: string
  name: string
  status: 'draft' | 'approved' | 'rejected' | 'old'
  created_at: string
  sec?: number
  registry?: string
  prompt?: string
  refs?: string[]
}

export interface ImgSet { images: AssetImage[]; error: string | null }

export interface Outfit {
  outfit_id: string
  name?: string
  desc?: string
  when?: string
  episodes?: number[]
  prompt_en?: string
  _img: ImgSet
  _default?: boolean
}

export interface RegCharacter {
  char_id: string
  name: string
  tier?: string
  age?: number
  apparent_age?: string
  face?: Record<string, string> | string
  hair?: string
  body?: Record<string, string> | string
  signature_props?: string[]
  invariants?: string[]
  wardrobe: Outfit[]
  prompt_en?: string
  inferred?: string[]
  _img: ImgSet
  _matrix: string[]
}

export interface Variant { variant_id: string; time_of_day?: string; lighting?: string; prompt_en?: string; _img: ImgSet }

export interface RegLocation {
  loc_id: string
  bible_id?: string | null
  name: string
  parent?: string | null
  int_ext?: string
  desc?: string
  layout?: string
  fixed_elements?: string[]
  aliases?: string[]
  variants: Variant[]
  prompt_en?: string
  _scenes: string[]
}

export interface RegProp { prop_id: string; name: string; desc?: string; owner?: string | null; episodes?: number[]; prompt_en?: string; _img: ImgSet }

export interface SceneMapRow {
  episode: number
  scene: string
  loc_id: string | null
  variant_id?: string | null
  characters?: Record<string, string>
  referenced?: string[]
  props?: string[]
}

export interface Issue { severity: 'high' | 'medium' | 'low'; type?: string; where?: string; problem?: string; fix?: string }

export interface Registry {
  series?: string
  version: number
  style?: Record<string, string>
  characters: RegCharacter[]
  locations: RegLocation[]
  props: RegProp[]
  scene_map: SceneMapRow[]
  issues: Issue[]
  [k: string]: unknown
}

export interface AssetsView {
  registry: { reg: Registry; file: string; episodes: number[]; pending: Record<string, number>; counts: Record<string, number> } | null
  codex: boolean
  base: string
}

export type AssetKind = 'character' | 'outfit' | 'location' | 'prop'

export interface NewProject { slug: string; title: string; idea: string; episodes: number; episode_sec: number }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  if (!res.ok) {
    let msg = res.statusText
    try {
      const body = await res.json()
      msg = body.detail || msg
    } catch { /* not json */ }
    throw new ApiError(res.status, msg)
  }
  return res.json() as Promise<T>
}

const p = (slug: string, sid: string) => `/projects/${encodeURIComponent(slug)}/${encodeURIComponent(sid)}`

export const api = {
  health: () => request<{ ok: boolean; env: Record<string, unknown> }>('/health'),
  projects: () => request<ProjectSummary[]>('/projects'),
  createProject: (body: NewProject) =>
    request<{ slug: string; session_id: string; job: Job }>('/projects', { method: 'POST', body: JSON.stringify(body) }),
  skills: () => request<Skill[]>('/skills'),
  analyses: () => request<Analysis[]>('/analyses'),
  hide: (kind: 'runs' | 'series' | 'jobs' | 'skills', item: string) =>
    request<{ ok: boolean }>('/hide', { method: 'POST', body: JSON.stringify({ kind, item }) }),
  unhide: (kind: 'runs' | 'series' | 'jobs' | 'skills', item: string) =>
    request<{ ok: boolean }>('/unhide', { method: 'POST', body: JSON.stringify({ kind, item }) }),
  hidden: () => request<Record<'runs' | 'series' | 'jobs' | 'skills', string[]>>('/hidden'),
  project: (slug: string, sid: string) => request<Project>(p(slug, sid)),
  doc: (slug: string, sid: string, kind: string, v = 0) => request<DocResponse>(`${p(slug, sid)}/docs/${kind}${v ? `?v=${v}` : ''}`),
  episode: (slug: string, sid: string, n: number, v = 0) =>
    request<EpisodeResponse>(`${p(slug, sid)}/episodes/${n}${v ? `?v=${v}` : ''}`),
  refine: (slug: string, sid: string, body: { feedback?: string; target?: string; approve?: string | null }) =>
    request<Job>(`${p(slug, sid)}/refine`, { method: 'POST', body: JSON.stringify(body) }),
  comments: (slug: string, sid: string, episode?: number) =>
    request<Comment[]>(`${p(slug, sid)}/comments${episode ? `?episode=${episode}` : ''}`),
  addComment: (slug: string, sid: string, c: CommentDraft) =>
    request<Comment>(`${p(slug, sid)}/comments`, { method: 'POST', body: JSON.stringify(c) }),
  updateComment: (slug: string, sid: string, id: string, f: { text?: string; status?: 'open' | 'resolved' }) =>
    request<Comment>(`${p(slug, sid)}/comments/${id}`, { method: 'PATCH', body: JSON.stringify(f) }),
  deleteComment: (slug: string, sid: string, id: string) =>
    request<{ ok: boolean }>(`${p(slug, sid)}/comments/${id}`, { method: 'DELETE' }),
  sendComments: (slug: string, sid: string, body: { ids?: string[]; general?: string }) =>
    request<Job>(`${p(slug, sid)}/comments/send`, { method: 'POST', body: JSON.stringify(body) }),
  saveEpisode: (slug: string, sid: string, n: number, body: { base_version: number; data: EpisodeData; note?: string }) =>
    request<SaveResult>(`${p(slug, sid)}/episodes/${n}`, { method: 'PUT', body: JSON.stringify(body) }),
  assets: (slug: string, sid: string) => request<AssetsView>(`${p(slug, sid)}/assets`),
  generateImages: (slug: string, sid: string, body: { kinds?: AssetKind[]; ids?: string[]; force?: boolean }) =>
    request<Job>(`${p(slug, sid)}/assets/images`, { method: 'POST', body: JSON.stringify(body) }),
  reviewImages: (slug: string, sid: string, files: string[], status: 'approved' | 'rejected' | 'draft') =>
    request<{ updated: number }>(`${p(slug, sid)}/assets/review`, { method: 'POST', body: JSON.stringify({ files, status }) }),
  buildAssets: (slug: string, sid: string, feedback = '') =>
    request<Job>(`${p(slug, sid)}/assets/build`, { method: 'POST', body: JSON.stringify({ feedback }) }),
  saveAssets: (slug: string, sid: string, base_file: string, data: Registry, note = '') =>
    request<{ file: string; version: number; warnings: string[] }>(`${p(slug, sid)}/assets`,
      { method: 'PUT', body: JSON.stringify({ base_file, data, note }) }),
  jobs: (limit = 30) => request<Job[]>(`/jobs?limit=${limit}`),
  job: (id: string) => request<JobDetail>(`/jobs/${id}`),
  cancelJob: (id: string) => request<{ ok: boolean }>(`/jobs/${id}/cancel`, { method: 'POST' }),
  resumeJob: (id: string) => request<Job>(`/jobs/${id}/resume`, { method: 'POST' }),
}

export const qk = {
  projects: ['projects'] as const,
  skills: ['skills'] as const,
  analyses: ['analyses'] as const,
  hidden: ['hidden'] as const,
  project: (slug: string, sid: string) => ['project', slug, sid] as const,
  doc: (slug: string, sid: string, kind: string, v: number) => ['doc', slug, sid, kind, v] as const,
  episode: (slug: string, sid: string, n: number, v: number) => ['episode', slug, sid, n, v] as const,
  comments: (slug: string, sid: string) => ['comments', slug, sid] as const,
  assets: (slug: string, sid: string) => ['assets', slug, sid] as const,
  jobs: ['jobs'] as const,
  job: (id: string) => ['job', id] as const,
}

/** Old Jinja pages that the new UI has not replaced yet. */
export const legacy = {
  home: '/',
  seriesNew: '/series/new',
  analyzeNew: '/analyze/new',
  project: (slug: string, sid: string, view = '') => `/series/${slug}/${sid}${view ? `?view=${view}` : ''}`,
  job: (id: string) => `/jobs/${id}`,
}
