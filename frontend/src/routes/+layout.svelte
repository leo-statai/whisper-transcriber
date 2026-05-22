<script lang="ts">
  import '../app.css';
  import { t } from '$lib/i18n/pt-BR';
  import { page } from '$app/state';
  import { AudioLines, Home, Upload, Moon, Sun } from 'lucide-svelte';
  import { cn } from '$lib/utils';

  let { children } = $props();

  let dark = $state(true);

  $effect(() => {
    if (typeof document === 'undefined') return;
    dark = document.documentElement.classList.contains('dark');
  });

  function toggleTheme() {
    const root = document.documentElement;
    root.classList.toggle('dark');
    dark = root.classList.contains('dark');
    try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (_) {}
  }

  function isActive(path: string): boolean {
    if (path === '/') return page.url.pathname === '/';
    return page.url.pathname.startsWith(path);
  }
</script>

<div class="min-h-full flex flex-col">
  <header class="border-b border-[var(--color-border)] bg-[var(--color-bg-elev)]/80 backdrop-blur sticky top-0 z-20">
    <div class="max-w-5xl mx-auto px-6 h-14 flex items-center gap-4">
      <a href="/" class="flex items-center gap-2 font-semibold">
        <span class="inline-flex items-center justify-center w-8 h-8 rounded-[var(--radius-md)] bg-[var(--color-accent)]/15 text-[var(--color-accent)]">
          <AudioLines size={18} />
        </span>
        {t.appName}
      </a>
      <nav class="flex items-center gap-1 ml-4 text-sm">
        <a
          href="/"
          class={cn(
            'px-3 h-9 inline-flex items-center gap-1.5 rounded-[var(--radius-md)] transition-colors',
            isActive('/') && !isActive('/upload')
              ? 'bg-[var(--color-bg-elev-2)] text-[var(--color-fg)]'
              : 'text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]'
          )}
        >
          <Home size={16} /> {t.nav.dashboard}
        </a>
        <a
          href="/upload"
          class={cn(
            'px-3 h-9 inline-flex items-center gap-1.5 rounded-[var(--radius-md)] transition-colors',
            isActive('/upload')
              ? 'bg-[var(--color-bg-elev-2)] text-[var(--color-fg)]'
              : 'text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]'
          )}
        >
          <Upload size={16} /> {t.nav.upload}
        </a>
      </nav>
      <div class="ml-auto">
        <button
          onclick={toggleTheme}
          class="w-9 h-9 inline-flex items-center justify-center rounded-[var(--radius-md)] text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] hover:bg-[var(--color-bg-elev-2)]"
          aria-label={dark ? 'Modo claro' : 'Modo escuro'}
        >
          {#if dark}
            <Sun size={18} />
          {:else}
            <Moon size={18} />
          {/if}
        </button>
      </div>
    </div>
  </header>

  <main class="flex-1 max-w-5xl mx-auto w-full px-6 py-8">
    {@render children?.()}
  </main>

  <footer class="border-t border-[var(--color-border)] py-4 text-center text-xs text-[var(--color-fg-muted)]">
    {t.appName} · {t.tagline}
  </footer>
</div>
