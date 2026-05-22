<script lang="ts">
  import { goto } from '$app/navigation';
  import { TUSD_URL } from '$lib/config';
  import { languages, t } from '$lib/i18n/pt-BR';
  import { formatBytes } from '$lib/utils';
  import { Upload as UploadIcon, Pause, Play, X, Loader2 } from 'lucide-svelte';
  import * as tus from 'tus-js-client';
  import Button from './Button.svelte';
  import ProgressBar from './ProgressBar.svelte';

  let dragOver = $state(false);
  let file = $state<File | null>(null);
  let language = $state('');
  let upload = $state<tus.Upload | null>(null);
  let progress = $state(0);
  let bytesSent = $state(0);
  let bytesTotal = $state(0);
  let state = $state<'idle' | 'uploading' | 'paused' | 'done' | 'error'>('idle');
  let errorMsg = $state<string | null>(null);
  let inputEl: HTMLInputElement | undefined = $state();

  function reset() {
    file = null;
    upload?.abort();
    upload = null;
    progress = 0;
    bytesSent = 0;
    bytesTotal = 0;
    state = 'idle';
    errorMsg = null;
  }

  function pickFile(f: File) {
    file = f;
    state = 'idle';
    errorMsg = null;
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    dragOver = false;
    const f = e.dataTransfer?.files?.[0];
    if (f) pickFile(f);
  }

  function start() {
    if (!file) return;
    const f = file;
    state = 'uploading';
    errorMsg = null;

    const u = new tus.Upload(f, {
      endpoint: TUSD_URL,
      retryDelays: [0, 1000, 3000, 5000, 10000],
      chunkSize: 8 * 1024 * 1024,
      metadata: {
        filename: f.name,
        filetype: f.type || 'application/octet-stream',
        language
      },
      onError: (err) => {
        state = 'error';
        errorMsg = err.message || t.upload.failed;
      },
      onProgress: (sent, total) => {
        bytesSent = sent;
        bytesTotal = total;
        progress = total > 0 ? (sent / total) * 100 : 0;
      },
      onSuccess: async () => {
        state = 'done';
        progress = 100;
        // tusd dispara post-finish que cria o Job no backend.
        // Damos um pequeno tempo e voltamos para o dashboard.
        setTimeout(() => goto('/'), 800);
      }
    });
    upload = u;
    u.start();
  }

  function pause() {
    upload?.abort();
    state = 'paused';
  }

  function resume() {
    if (!file) return;
    state = 'uploading';
    upload?.start();
  }

  function cancel() {
    upload?.abort(true);
    reset();
  }
</script>

<div class="w-full max-w-2xl mx-auto">
  {#if !file}
    <button
      type="button"
      class="w-full aspect-[2.4/1] flex flex-col items-center justify-center gap-3
             rounded-[var(--radius-lg)] border-2 border-dashed transition-colors
             {dragOver
               ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/5'
               : 'border-[var(--color-border)] hover:border-[var(--color-fg-muted)] bg-[var(--color-bg-elev)]'}"
      ondragover={(e) => { e.preventDefault(); dragOver = true; }}
      ondragleave={() => (dragOver = false)}
      ondrop={onDrop}
      onclick={() => inputEl?.click()}
      aria-label={t.upload.selectButton}
    >
      <UploadIcon size={40} class="text-[var(--color-fg-muted)]" />
      <p class="text-base font-medium">{dragOver ? t.upload.dropHere : t.upload.helper}</p>
      <p class="text-xs text-[var(--color-fg-muted)]">{t.upload.selectButton}</p>
    </button>
    <input
      type="file"
      accept="audio/*,video/*,.mp3,.wav,.m4a,.flac,.ogg,.opus,.aac,.mp4,.mkv,.mov,.webm,.avi"
      class="hidden"
      bind:this={inputEl}
      onchange={(e) => {
        const f = (e.currentTarget as HTMLInputElement).files?.[0];
        if (f) pickFile(f);
      }}
    />
  {:else}
    <div class="rounded-[var(--radius-lg)] bg-[var(--color-bg-elev)] border border-[var(--color-border)] p-5 space-y-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="font-medium truncate" title={file.name}>{file.name}</p>
          <p class="text-xs text-[var(--color-fg-muted)] mt-0.5">{formatBytes(file.size)}</p>
        </div>
        {#if state !== 'uploading'}
          <button
            type="button"
            class="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
            onclick={cancel}
            aria-label={t.upload.cancel}
          >
            <X size={20} />
          </button>
        {/if}
      </div>

      {#if state === 'idle'}
        <div>
          <label for="lang" class="block text-sm mb-1.5">{t.upload.languageLabel}</label>
          <select
            id="lang"
            bind:value={language}
            class="w-full h-10 rounded-[var(--radius-md)] bg-[var(--color-bg-elev-2)] border border-[var(--color-border)] px-3 text-sm focus:border-[var(--color-accent)] outline-none"
          >
            {#each languages as l}
              <option value={l.code}>{l.label}</option>
            {/each}
          </select>
        </div>
        <Button onclick={start} class="w-full">
          <UploadIcon size={16} />
          {t.upload.start}
        </Button>
      {/if}

      {#if state === 'uploading' || state === 'paused'}
        <ProgressBar value={progress} label={`${t.upload.progress}: ${formatBytes(bytesSent)} / ${formatBytes(bytesTotal)}`} />
        <div class="flex gap-2">
          {#if state === 'uploading'}
            <Button variant="secondary" onclick={pause} class="flex-1"><Pause size={16}/>{t.upload.pause}</Button>
          {:else}
            <Button variant="secondary" onclick={resume} class="flex-1"><Play size={16}/>{t.upload.resume}</Button>
          {/if}
          <Button variant="danger" onclick={cancel} class="flex-1"><X size={16}/>{t.upload.cancel}</Button>
        </div>
      {/if}

      {#if state === 'done'}
        <div class="flex items-center gap-2 text-[var(--color-accent)] text-sm">
          <Loader2 size={16} class="animate-spin" />
          {t.upload.success}
        </div>
      {/if}

      {#if state === 'error'}
        <p class="text-sm text-[var(--color-danger)]">{errorMsg || t.upload.failed}</p>
        <Button onclick={start} class="w-full">Tentar novamente</Button>
      {/if}
    </div>
  {/if}
</div>
