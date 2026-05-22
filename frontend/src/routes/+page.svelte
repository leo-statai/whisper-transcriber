<script lang="ts">
  import { api, type Job } from '$lib/api';
  import Button from '$lib/components/Button.svelte';
  import JobCard from '$lib/components/JobCard.svelte';
  import { t } from '$lib/i18n/pt-BR';
  import { onMount, onDestroy } from 'svelte';
  import { RefreshCw, Plus, Inbox } from 'lucide-svelte';

  let jobs = $state<Job[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let timer: ReturnType<typeof setInterval> | undefined;

  async function load() {
    try {
      jobs = await api.listJobs();
      error = null;
    } catch (e: any) {
      error = e.message || t.errors.generic;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    load();
    timer = setInterval(load, 4000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });

  const hasActive = $derived(jobs.some((j) => j.status === 'processing' || j.status === 'queued'));
</script>

<div class="flex items-center justify-between mb-6">
  <div>
    <h1 class="text-2xl font-semibold">{t.dashboard.title}</h1>
    {#if hasActive}
      <p class="text-sm text-[var(--color-fg-muted)] mt-1">
        Transcrição em andamento — atualizando automaticamente
      </p>
    {/if}
  </div>
  <div class="flex items-center gap-2">
    <Button variant="ghost" onclick={load} aria-label={t.dashboard.refresh}>
      <RefreshCw size={16} class={loading ? 'animate-spin' : ''} />
    </Button>
    <a href="/upload">
      <Button>
        <Plus size={16} />
        {t.dashboard.newJob}
      </Button>
    </a>
  </div>
</div>

{#if error}
  <div class="rounded-[var(--radius-md)] border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 text-[var(--color-danger)] p-4 text-sm">
    {error}
  </div>
{:else if loading && jobs.length === 0}
  <div class="space-y-3">
    {#each Array(3) as _}
      <div class="h-20 rounded-[var(--radius-lg)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] animate-pulse"></div>
    {/each}
  </div>
{:else if jobs.length === 0}
  <div class="text-center py-20">
    <div class="inline-flex w-14 h-14 items-center justify-center rounded-full bg-[var(--color-bg-elev-2)] text-[var(--color-fg-muted)] mb-4">
      <Inbox size={26} />
    </div>
    <p class="text-[var(--color-fg-muted)] mb-6">{t.dashboard.empty}</p>
    <a href="/upload">
      <Button><Plus size={16} />{t.dashboard.newJob}</Button>
    </a>
  </div>
{:else}
  <div class="space-y-3">
    {#each jobs as job (job.id)}
      <JobCard {job} />
    {/each}
  </div>
{/if}
