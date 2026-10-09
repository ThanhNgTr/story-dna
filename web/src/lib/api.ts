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

export interface ContinueBody {
  slug: string
  sid: string
  title: string
  episode_sec: number
  canon_mode: 'transcript' | 'none' | 'full'
  source: 'videos' | 'run'
  video_path: string
  run_id: string
  language: string
  produced_upto: number
  new_episodes: number
  direction: 'follow' | 'new-arc'
  idea: string
  notes: string
  update_skill: boolean
}

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
  has_prompts: boolean
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
  story_check: StoryCheck | null
  editor: EditorSummary | null
  job: Job | null
}

export type EditorDim = 'theme' | 'protagonist' | 'supporting_cast' | 'antagonist' | 'dialogue'
  | 'setup_payoff' | 'stakes' | 'emotion' | 'originality'

export interface EditorSummary {
  file: string
  stage: 'outline' | 'episodes'
  verdict: 'pass' | 'revise'
  average: number
  stale: boolean
  scores: Partial<Record<EditorDim, number>>
  findings: { high: number; medium: number; low: number }
  applied: number
}

export interface EditorFinding {
  id: string
  dimension: EditorDim
  severity: 'high' | 'medium' | 'low'
  where: { file: string; episode?: number | null; scene?: string | null; field?: string | null }
  evidence: string
  problem: string
  fix: string
  affects?: string[]
}

export interface EditorReview {
  file: string
  versions: number[]
  stage: 'outline' | 'episodes'
  created_at: string
  summary: string
  theme_statement: string
  scores: Record<EditorDim, { score: number; why: string; evidence: string[] }>
  average: number
  verdict: 'pass' | 'revise'
  setup_payoff_map?: { plant: string; plant_ep?: number | null; payoff?: string | null; payoff_ep?: number | null }[]
  findings: EditorFinding[]
  strengths: string[]
  applied: string[]
  stale: boolean
}

export interface DialogueItem {
  episode: number
  scene: string | null
  character: string | null
  voiceover?: boolean
  line: string | null
  issues: string[]
  note?: string
  name?: string | null
}

export interface DialogueChange {
  episode: number
  scene?: string
  character?: string
  voiceover?: boolean
  before: string
  after: string
  why?: string
  name?: string | null
}

export interface DialogueView {
  checked_at: string
  counts: Record<string, number>
  items: DialogueItem[]
  episodes: Record<string, { lines: number; short_pct: number }>
  last_polish: { file: string; created_at?: string; episodes?: number[]; changes: DialogueChange[] } | null
  examples: number
}

export interface StoryCheck { ok: boolean; stage: 'outline' | 'episodes'; checked_at: string; errors: string[]; warnings: string[] }

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
  tagline_vi?: string | null
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
  title_vi?: string | null
  genre_vi?: string | null
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

// ----- reference videos + writing styles -----

export interface BrowseEntry { name: string; path: string; dir: boolean; size_mb?: number }
export interface BrowseResult { cwd: string; parent: string | null; entries: BrowseEntry[]; n_videos: number; input_dir: string }
export interface Estimate { units: number; transcribe: string; analysts: string; merge: string; total: string }
export interface ProbeResult {
  path: string
  is_dir: boolean
  items: { name: string; duration_sec: number | null }[]
  minutes: number
  estimate: Estimate | null
  existing: { id: string; title: string | null; sources: string[]; done: boolean; analyzed: number; units: number }[]
}

export interface RunSummaryVi {
  title_vi?: string
  genre_vi?: string
  logline_vi?: string
  synopsis_vi?: string
  characters?: { name: string; tier?: string; role_vi?: string; desc_vi?: string }[]
  why_it_hooks_vi?: string[]
  style_vi?: Record<'story' | 'pacing' | 'camera' | 'sound' | 'color', string>
  episodes_hint_vi?: string
}

export interface AnalysisDetail {
  id: string
  title: string | null
  genre: string | null
  logline: string | null
  sources: { filename: string; duration_sec: number | null }[]
  minutes: number | null
  language: string | null
  units: { id: string; start: number; end: number; source?: string; done: boolean }[]
  done: boolean
  skills: string[]
  docs: Record<'story' | 'dna' | 'analysis', boolean>
  characters: { name: string; tier?: string }[]
  summary_vi: RunSummaryVi | null
  suggested_slug: string
  job: Job | null
}

export interface SkillSummaryVi {
  version?: string
  tagline_vi?: string
  description_vi?: string
  best_for_vi?: string[]
  not_for_vi?: string[]
  rules_vi?: Record<string, string[]>
}

export interface SkillDetail extends Omit<Skill, 'reference' | 'projects'> {
  versions: { version: string; created: string | null; changes: string[]; stable: boolean }[]
  projects: { slug: string; session_id: string; title: string }[]
  reference: { id: string; title: string | null; minutes: number } | null
  summary_vi: SkillSummaryVi | null
  summary_stale: boolean
  skill_md: string
}

export interface NewProject { slug: string; title: string; idea: string; episodes: number; episode_sec: number }

export class ApiError extends Error {
  status: number
  data: unknown
  constructor(status: number, message: string, data?: unknown) {
    super(message)
    this.status = status
    this.data = data
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  if (!res.ok) {
    let msg = res.statusText
    let data: unknown
    try {
      const body = await res.json()
      data = body.detail
      msg = typeof body.detail === 'string' ? body.detail : body.detail?.message || msg
    } catch { /* not json */ }
    throw new ApiError(res.status, msg, data)
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
  continueSeries: (body: ContinueBody) =>
    request<{ slug: string; session_id: string; job: Job }>('/continue', { method: 'POST', body: JSON.stringify(body) }),
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
  editor: (slug: string, sid: string) => request<EditorReview>(`${p(slug, sid)}/editor`),
  runEditor: (slug: string, sid: string, body: { mode: 'review' | 'apply'; ids?: string[]; rereview?: boolean }) =>
    request<Job>(`${p(slug, sid)}/editor`, { method: 'POST', body: JSON.stringify(body) }),
  dialogue: (slug: string, sid: string) => request<DialogueView>(`${p(slug, sid)}/dialogue`),
  polishDialogue: (slug: string, sid: string, episodes: number[] = []) =>
    request<Job>(`${p(slug, sid)}/dialogue/polish`, { method: 'POST', body: JSON.stringify({ episodes }) }),
  makeShotlist: (slug: string, sid: string, episodes: number[] = [], force = false) =>
    request<Job>(`${p(slug, sid)}/shotlist`, { method: 'POST', body: JSON.stringify({ episodes, force }) }),
  packageUrl: (slug: string, sid: string, n: number) => `/api${p(slug, sid)}/episodes/${n}/package`,
  fixStory: (slug: string, sid: string) => request<Job>(`${p(slug, sid)}/story/fix`, { method: 'POST' }),
  buildAssets: (slug: string, sid: string, feedback = '') =>
    request<Job>(`${p(slug, sid)}/assets/build`, { method: 'POST', body: JSON.stringify({ feedback }) }),
  saveAssets: (slug: string, sid: string, base_file: string, data: Registry, note = '') =>
    request<{ file: string; version: number; warnings: string[] }>(`${p(slug, sid)}/assets`,
      { method: 'PUT', body: JSON.stringify({ base_file, data, note }) }),
  browse: (path = '') => request<BrowseResult>(`/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`),
  probe: (path: string) => request<ProbeResult>(`/probe?path=${encodeURIComponent(path)}`),
  startAnalysis: (body: { video_path: string; language: string; chunk_sec: number; max_frames: number; force?: boolean }) =>
    request<Job>('/analyses', { method: 'POST', body: JSON.stringify(body) }),
  analysis: (id: string) => request<AnalysisDetail>(`/analyses/${id}`),
  analysisDoc: (id: string, kind: string) => request<{ kind: string; markdown: string }>(`/analyses/${id}/doc/${kind}`),
  resumeAnalysis: (id: string) => request<Job>(`/analyses/${id}/resume`, { method: 'POST' }),
  createSkill: (body: { run_id: string; slug: string; update: boolean }) =>
    request<Job>('/skills', { method: 'POST', body: JSON.stringify(body) }),
  skill: (slug: string) => request<SkillDetail>(`/skills/${slug}`),
  summarize: (target: 'run' | 'skill', id: string) =>
    request<Job>('/summaries', { method: 'POST', body: JSON.stringify({ target, id, force: true }) }),
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
  editor: (slug: string, sid: string) => ['editor', slug, sid] as const,
  dialogue: (slug: string, sid: string) => ['dialogue', slug, sid] as const,
  analysis: (id: string) => ['analysis', id] as const,
  skill: (slug: string) => ['skill', slug] as const,
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

/** Upload one video file with progress (fetch has no upload progress). Resolves to the saved path. */
export function uploadVideo(file: File, folder: string, onProgress: (pct: number) => void): Promise<{ path: string; folder: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/uploads?name=${encodeURIComponent(file.name)}&folder=${encodeURIComponent(folder)}`)
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((100 * e.loaded) / e.total))
    xhr.onload = () => {
      let body: { detail?: string; path?: string; folder?: string } = {}
      try { body = JSON.parse(xhr.responseText) } catch { /* not json */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as { path: string; folder: string })
      else reject(new ApiError(xhr.status, body.detail || xhr.statusText))
    }
    xhr.onerror = () => reject(new ApiError(0, 'Mất kết nối khi tải lên.'))
    xhr.send(file)
  })
}

export const LANGUAGES: [string, string][] = [
  ['', 'Tự nhận diện'], ['vi', 'Tiếng Việt'], ['en', 'Tiếng Anh'], ['zh', 'Tiếng Trung'], ['ko', 'Tiếng Hàn'], ['ja', 'Tiếng Nhật'], ['th', 'Tiếng Thái'],
]
