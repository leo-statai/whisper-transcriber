import { API_URL } from './config';

export type JobStatus = 'queued' | 'processing' | 'done' | 'failed' | 'cancelled';

export interface Segment {
  idx: number;
  start: number;
  end: number;
  text: string;
}

export interface Job {
  id: string;
  filename: string;
  size_bytes: number;
  status: JobStatus;
  progress_pct: number;
  language: string | null;
  detected_language: string | null;
  model: string;
  duration_seconds: number | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface JobDetail extends Job {
  segments: Segment[];
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) }
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${txt}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  listJobs: () => req<Job[]>('/jobs'),
  getJob: (id: string) => req<JobDetail>(`/jobs/${id}`),
  cancelJob: (id: string) => req<{ ok: boolean }>(`/jobs/${id}/cancel`, { method: 'POST' }),
  deleteJob: (id: string) => req<{ ok: boolean }>(`/jobs/${id}`, { method: 'DELETE' }),
  exportUrl: (id: string, format: string) => `${API_URL}/jobs/${id}/export?format=${format}`
};
