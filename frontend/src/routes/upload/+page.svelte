<script lang="ts">
  import Uploader from '$lib/components/Uploader.svelte';
  import { t } from '$lib/i18n/pt-BR';
</script>

<div class="space-y-6">
  <div>
    <h1 class="text-2xl font-semibold">{t.upload.title}</h1>
    <p class="text-sm text-[var(--color-fg-muted)] mt-1">
      Após o envio, a transcrição começa automaticamente. Você pode acompanhar em tempo real.
    </p>
  </div>
  <Uploader />
</div>
