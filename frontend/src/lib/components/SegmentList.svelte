<script lang="ts">
  import type { Segment } from '$lib/api';
  import { formatTs } from '$lib/utils';
  import { tick } from 'svelte';

  interface Props {
    segments: Segment[];
    live?: boolean;
  }
  let { segments, live = false }: Props = $props();

  let container: HTMLDivElement | undefined = $state();

  $effect(() => {
    if (live && container) {
      tick().then(() => {
        container?.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
      });
    }
    // depend on length so effect runs when new segments arrive
    segments.length;
  });
</script>

<div
  bind:this={container}
  class="max-h-[60vh] overflow-y-auto rounded-[var(--radius-md)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] divide-y divide-[var(--color-border)]"
>
  {#if segments.length === 0}
    <div class="p-8 text-center text-[var(--color-fg-muted)] text-sm">
      {#if live}
        <span class="inline-block animate-pulse">Aguardando primeiros segmentos…</span>
      {:else}
        Sem segmentos.
      {/if}
    </div>
  {:else}
    {#each segments as seg (seg.idx)}
      <div class="px-4 py-3 grid grid-cols-[auto_1fr] gap-3 items-baseline hover:bg-[var(--color-bg-elev-2)]/40">
        <span class="text-xs font-mono tabular-nums text-[var(--color-fg-muted)] whitespace-nowrap">
          {formatTs(seg.start)}
        </span>
        <p class="text-sm leading-relaxed text-[var(--color-fg)]">{seg.text}</p>
      </div>
    {/each}
  {/if}
</div>
