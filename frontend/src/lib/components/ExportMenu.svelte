<script lang="ts">
  import { api } from '$lib/api';
  import { t } from '$lib/i18n/pt-BR';
  import { Download, FileText, FileJson, FileType, Subtitles } from 'lucide-svelte';
  import Button from './Button.svelte';

  interface Props { jobId: string; disabled?: boolean; }
  let { jobId, disabled = false }: Props = $props();

  let open = $state(false);
  let container: HTMLDivElement | undefined = $state();

  const items = [
    { format: 'srt', label: t.export.srt, icon: Subtitles },
    { format: 'vtt', label: t.export.vtt, icon: Subtitles },
    { format: 'txt', label: t.export.txt, icon: FileText },
    { format: 'json', label: t.export.json, icon: FileJson },
    { format: 'docx', label: t.export.docx, icon: FileType }
  ] as const;

  function onWindowClick(e: MouseEvent) {
    if (container && !container.contains(e.target as Node)) open = false;
  }

  $effect(() => {
    if (open) {
      window.addEventListener('click', onWindowClick);
      return () => window.removeEventListener('click', onWindowClick);
    }
  });
</script>

<div class="relative" bind:this={container}>
  <Button variant="secondary" {disabled} onclick={() => (open = !open)}>
    <Download size={16} />
    {t.job.export}
  </Button>
  {#if open && !disabled}
    <div
      class="absolute right-0 mt-2 w-56 z-10 rounded-[var(--radius-md)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] shadow-lg overflow-hidden"
      role="menu"
    >
      {#each items as item}
        <a
          role="menuitem"
          href={api.exportUrl(jobId, item.format)}
          class="flex items-center gap-2.5 px-3 py-2.5 text-sm hover:bg-[var(--color-bg-elev-2)] transition-colors"
          onclick={() => (open = false)}
        >
          <item.icon size={16} class="text-[var(--color-fg-muted)]" />
          {item.label}
          <span class="ml-auto text-xs text-[var(--color-fg-muted)] uppercase">{item.format}</span>
        </a>
      {/each}
    </div>
  {/if}
</div>
