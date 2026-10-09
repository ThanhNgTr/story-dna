import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { toast } from 'sonner'
import { qk, type Job } from './api'
import { JOB_STATUS } from './format'

/**
 * One EventSource for the whole app: keeps the job list fresh, refreshes a project when one of its
 * jobs finishes, and shows a toast (+ a browser notification when the tab is hidden).
 */
export function useJobsStream() {
  const qc = useQueryClient()
  const prev = useRef<Map<string, Job['status']>>(new Map())
  const imagesDone = useRef<Map<string, number>>(new Map())

  useEffect(() => {
    const es = new EventSource('/api/events')
    es.addEventListener('jobs', (ev) => {
      const jobs: Job[] = JSON.parse((ev as MessageEvent).data)
      qc.setQueryData(qk.jobs, jobs)
      const seen = prev.current
      for (const j of jobs) {
        const before = seen.get(j.id)
        if (before === 'running' && j.status !== 'running') {
          if (j.slug && j.session_id) {
            qc.invalidateQueries({ queryKey: ['project', j.slug, j.session_id] })
            qc.invalidateQueries({ queryKey: ['episode', j.slug, j.session_id] })
            qc.invalidateQueries({ queryKey: ['doc', j.slug, j.session_id] })
            qc.invalidateQueries({ queryKey: ['assets', j.slug, j.session_id] })
            qc.invalidateQueries({ queryKey: ['editor', j.slug, j.session_id] })
            qc.invalidateQueries({ queryKey: ['dialogue', j.slug, j.session_id] })
          }
          for (const k of [qk.projects, qk.skills, qk.analyses, ['analysis'], ['skill']]) qc.invalidateQueries({ queryKey: k })
          const st = JOB_STATUS[j.status]
          const msg = `${j.title}: ${st.label.toLowerCase()}`
          if (j.status === 'done') toast.success(msg)
          else toast.error(msg, { description: j.error ?? undefined })
          if (document.hidden && 'Notification' in window && Notification.permission === 'granted') {
            new Notification('story-dna', { body: msg })
          }
        }
        if (before !== 'running' && j.status === 'running' && j.slug && j.session_id) {
          qc.invalidateQueries({ queryKey: ['project', j.slug, j.session_id] })
        }
        // Image jobs: refresh the looks pages as each image lands, not only at the end
        const done = Number(j.steps.images?.done ?? 0)
        if (j.kind === 'images' && j.slug && j.session_id && done !== (imagesDone.current.get(j.id) ?? done)) {
          qc.invalidateQueries({ queryKey: ['assets', j.slug, j.session_id] })
        }
        imagesDone.current.set(j.id, done)
        // Shotlist: each episode's download button appears as soon as its prompts exist
        const shots = Number(j.steps.shotlist?.done ?? 0)
        if (j.kind === 'shotlist' && j.slug && j.session_id && shots !== (imagesDone.current.get(`${j.id}:shots`) ?? shots)) {
          qc.invalidateQueries({ queryKey: ['project', j.slug, j.session_id] })
        }
        imagesDone.current.set(`${j.id}:shots`, shots)
        // Analysis: units finish one by one; keep the video page in step
        if (j.kind === 'analysis' && j.status === 'running') qc.invalidateQueries({ queryKey: ['analysis'] })
        seen.set(j.id, j.status)
      }
    })
    return () => es.close()
  }, [qc])
}

export function askNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    void Notification.requestPermission()
  }
}
