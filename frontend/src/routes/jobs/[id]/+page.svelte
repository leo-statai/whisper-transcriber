<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { api, type JobDetail, type Segment } from '$lib/api';
  import { streamJob, type SseEvent } from '$lib/sse';
  import Badge from '$lib/components/Badge.svelte';
  import Button from '$lib/components/Button.svelte';
  import ProgressBar from '$lib/components/ProgressBar.svelte';
  import SegmentList from '$lib/components/SegmentList.svelte';
  import ExportMenu from '$lib/components/ExportMenu.svelte';
  import { t } from '$lib/i18n/pt-BR';
  import { formatBytes, formatDuration } from '$lib/utils';
  import { onDestroy, onMount } from 'svelte';
  import { ArrowLeft, Trash2, Ban } from 'lucide-svelte';

  const id = $derived(page.params.id);

  let job = $state<JobDetail | null>(null);
  let segments = $state<Segment[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let closeStream: (() => void) | null = null;

  async function loadInitial() {
    try {
      const j = await api.getJob(id);
      job = j;
      segments = [...j.segments];
      error = null;
    } catch (e: any) {
      error = e.message || t.errors.generic;
    } finally {
      loading = false;
    }
  }

  function handleEvent(e: SseEvent) {
    if (!job) return;
    switch (e.event) {
      case 'snapshot':
        job = { ...job, ...e.data } as JobDetail;
        break;
      case 'status':
        job = { ...job, status: e.data.status as any };
        break;
      case 'duration':
        job = { ...job, duration_seconds: e.data.seconds };
        break;
      case 'language':
        job = { ...job, detected_language: e.data.language };
        break;
      case 'progress':
        job = { ...job, progress_pct: e.data.pct };
        break;
      case 'segment':
        segments = [...segments, { idx: e.data.idx, start: e.data.start, end: e.data.end, text: e.data.text }];
        break;
      case 'done':
        job = { ...job, status: 'done', progress_pct: 100 };
        // Recarrega para metadados finais
        loadInitial();
        break;
      case 'failed':
        job = { ...job, status: 'failed', error: e.data.error };
        break;
      case 'cancelled':
        job = { ...job, status: 'cancelled' };
        break;
    }
  }

  onMount(async () => {
    await loadInitial();
    closeStream = streamJob(id, handleEvent);
  });

  onDestroy(() => closeStream?.());

  async function cancel() {
    if (!job) return;
    try { await api.cancelJob(id); } catch (e: any) { error = e.message; }
  }

  async function del() {
    if (!confirm(t.job.confirmDelete)) return;
    try {
      await api.deleteJob(id);
      goto('/');
    } catch (e: any) {
      error = e.message;
    }
  }

  const isLive = $derived(job?.status === 'processing' || job?.status === 'queued');
  const canCancel = $derived(job?.status === 'queued' || job?.status === 'processing');
  const canExport = $derived(job?.status === 'done' || (segments.length > 0));
</script>

<div class="space-y-6">
  <a href="/" class="inline-flex items-center gap-1.5 text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]">
    <ArrowLeft size={16} /> Voltar
  </a>

  {#if loading}
    <div class="h-32 rounded-[var(--radius-lg)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] animate-pulse"></div>
  {:else if !job}
    <p class="text-[var(--color-fg-muted)]">Job não encontrado.</p>
  {:else}
    <header class="rounded-[var(--radius-lg)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] p-5">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div class="min-w-0">
          <h1 class="text-xl font-semibold truncate" title={job.filename}>{job.filename}</h1>
          <div class="mt-1.5"><Badge status={job.status} /></div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          {#if canCancel}
            <Button variant="secondary" onclick={cancel}><Ban size={16}/>{t.job.cancel}</Button>
          {/if}
          {#if canExport}
            <ExportMenu jobId={id} />
          {/if}
          <Button variant="danger" onclick={del} aria-label={t.job.delete}><Trash2 size={16}/></Button>
        </div>
      </div>

      {#if isLive}
        <ProgressBar value={job.progress_pct} label={t.job.progress} indeterminate={!job.duration_seconds} />
      {/if}

      {#if job.error}
        <div class="mt-3 rounded-[var(--radius-md)] border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 text-[var(--color-danger)] p-3 text-sm">
          {job.error}
        </div>
      {/if}

      <dl class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">
        <div>
          <dt class="text-xs text-[var(--color-fg-muted)]">{t.job.duration}</dt>
          <dd class="font-medium tabular-nums">{formatDuration(job.duration_seconds)}</dd>
        </div>
        <div>
          <dt class="text-xs text-[var(--color-fg-muted)]">{t.job.language}</dt>
          <dd class="font-medium">{job.detected_language || job.language || '—'}</dd>
        </div>
        <div>
          <dt class="text-xs text-[var(--color-fg-muted)]">{t.job.model}</dt>
          <dd class="font-medium">{job.model}</dd>
        </div>
        <div>
          <dt class="text-xs text-[var(--color-fg-muted)]">{t.job.sizeOnDisk}</dt>
          <dd class="font-medium">{formatBytes(job.size_bytes)}</dd>
        </div>
      </dl>
    </header>

    <section>
      <h2 class="text-sm font-medium text-[var(--color-fg-muted)] uppercase tracking-wide mb-2">
        {t.job.segments}
        {#if segments.length > 0}
          <span class="ml-1 text-[var(--color-fg)] normal-case">({segments.length})</span>
        {/if}
      </h2>
      <SegmentList {segments} live={isLive} />
    </section>
  {/if}
</div>
