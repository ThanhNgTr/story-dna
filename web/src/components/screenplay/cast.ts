import type { EpisodeData } from '@/lib/api'

export interface CastMember { id: string; name: string; look?: string | null; offscreen?: boolean }

const VOICE_FALLBACK: Record<string, string> = {
  unknown_voice: 'Giọng trong loa',
  voice_unknown: 'Giọng trong loa',
  narrator: 'Người dẫn',
}

/** id -> display info, from the episode header plus voices without a character. */
export function castOf(ep: EpisodeData & { voices_without_character?: Record<string, string> }): Map<string, CastMember> {
  const m = new Map<string, CastMember>()
  for (const [id, c] of Object.entries(ep.characters ?? {})) {
    m.set(id, { id, name: c.name || id, look: c.visual_signature, offscreen: c.offscreen })
  }
  for (const [id, desc] of Object.entries(ep.voices_without_character ?? {})) {
    if (!m.has(id)) m.set(id, { id, name: VOICE_FALLBACK[id] ?? id, look: desc, offscreen: true })
  }
  return m
}

export function nameOf(cast: Map<string, CastMember>, id: string): string {
  return cast.get(id)?.name ?? VOICE_FALLBACK[id] ?? id
}

/** Stable hue per character id, so a character keeps its colour across episodes. */
export function hueOf(id: string): number {
  let h = 0
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) % 360
  return (h * 47) % 360
}

export const SHOT_LABEL: Record<string, string> = {
  ECU: 'Cận đặc tả', CU: 'Cận', MCU: 'Cận trung', MS: 'Trung', MWS: 'Trung rộng', WS: 'Rộng', EWS: 'Toàn',
  OTS: 'Qua vai', POV: 'Góc nhìn', INSERT: 'Chèn',
}
