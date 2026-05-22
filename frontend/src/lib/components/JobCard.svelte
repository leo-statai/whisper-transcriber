<script lang="ts">
  import type { Job } from '$lib/api';
  import Badge from './Badge.svelte';
  import ProgressBar from './ProgressBar.svelte';
  import { formatBytes, formatDuration, relativeTime } from '$lib/utils';
  import { FileAudio, FileVideo, Clock } from 'lucide-svelte';

  interface Props { job: Job; }
  let { job }: Props = $props();

  const isVideo = $derived(/\.(mp4|mkv|mov|webm|avi|m4v|wmv|mpg|mpeg|3gp|flv)$/i.test(job.filename));
</script>

<a
  href={`/jobs/${job.id}`}
  class="block group rounded-[var(--radius-lg)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] p-4 hover:border-[var(--color-accent)]/50 transition-colors"
>
  <div class="flex items-start gap-3">
    <div class="shrink-0 mt-1 text-[var(--color-fg-muted)] group-hover:text-[var(--color-accent)] transition-colors">
      {#if isVideo}
        <FileVideo size={20} />
      {:else}
        <FileAudio size={20} />
      {/if}
    </div>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2 mb-1">
        <h3 class="font-medium text-[var(--color-fg)] truncate" title={job.filename}>
          {job.filename}
        </h3>
      </div>
      <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--color-fg-muted)]">
        <Badge status={job.status} />
        <span>{formatBytes(job.size_bytes)}</span>
        {#if job.duration_seconds}
          <span class="inline-flex items-center gap-1"><Clock size={12} />{formatDuration(job.duration_seconds)}</span>
        {/if}
        <span>{relativeTime(job.created_at)}</span>
      </div>
      {#if job.status === 'processing'}
        <div class="mt-3">
          <ProgressBar value={job.progress_pct} />
        </div>
      {/if}
      {#if job.status === 'failed' && job.error}
        <p class="mt-2 text-xs text-[var(--color-danger)] line-clamp-2">{job.error}</p>
      {/if}
    </div>
  </div>
</a>
