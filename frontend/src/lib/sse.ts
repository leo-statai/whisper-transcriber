import { API_URL } from './config';

export type SseEvent =
  | { event: 'snapshot'; data: { status: string; progress_pct: number; duration_seconds: number | null; detected_language: string | null } }
  | { event: 'status'; data: { status: string } }
  | { event: 'duration'; data: { seconds: number } }
  | { event: 'language'; data: { language: string; probability: number } }
  | { event: 'segment'; data: { idx: number; start: number; end: number; text: string } }
  | { event: 'progress'; data: { pct: number } }
  | { event: 'done'; data: Record<string, never> }
  | { event: 'failed'; data: { error: string } }
  | { event: 'cancelled'; data: Record<string, never> }
  | { event: 'ping'; data: null };

export function streamJob(
  jobId: string,
  onEvent: (e: SseEvent) => void
): () => void {
  const url = `${API_URL}/jobs/${jobId}/stream`;
  const es = new EventSource(url);

  const handler = (name: SseEvent['event']) => (raw: MessageEvent) => {
    let data: any = null;
    try {
      data = raw.data ? JSON.parse(raw.data) : null;
    } catch {
      data = raw.data;
    }
    onEvent({ event: name, data } as SseEvent);
  };

  const events: SseEvent['event'][] = [
    'snapshot', 'status', 'duration', 'language',
    'segment', 'progress', 'done', 'failed', 'cancelled', 'ping'
  ];
  events.forEach((name) => es.addEventListener(name, handler(name)));

  return () => es.close();
}
