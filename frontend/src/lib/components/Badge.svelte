<script lang="ts">
  import { cn } from '$lib/utils';
  import { t } from '$lib/i18n/pt-BR';
  import type { JobStatus } from '$lib/api';

  interface Props {
    status: JobStatus;
    class?: string;
  }
  let { status, class: klass }: Props = $props();

  const styles: Record<JobStatus, string> = {
    queued: 'bg-[var(--color-bg-elev-2)] text-[var(--color-fg-muted)]',
    processing: 'bg-[var(--color-accent)]/15 text-[var(--color-accent)] animate-pulse',
    done: 'bg-[var(--color-accent)]/20 text-[var(--color-accent)]',
    failed: 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]',
    cancelled: 'bg-[var(--color-warn)]/15 text-[var(--color-warn)]'
  };
</script>

<span
  class={cn(
    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium select-none',
    styles[status],
    klass
  )}
>
  {t.status[status]}
</span>
