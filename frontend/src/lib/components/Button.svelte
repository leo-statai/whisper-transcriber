<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';

  interface Props extends HTMLButtonAttributes {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    children?: Snippet;
    class?: string;
  }

  let {
    variant = 'primary',
    size = 'md',
    children,
    class: klass,
    ...rest
  }: Props = $props();

  const base =
    'inline-flex items-center justify-center gap-2 font-medium rounded-[var(--radius-md)] transition-colors disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-2 focus-visible:outline-offset-2';

  const variants = {
    primary:
      'bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)]',
    secondary:
      'bg-[var(--color-bg-elev-2)] text-[var(--color-fg)] hover:bg-[var(--color-border)]',
    ghost:
      'bg-transparent text-[var(--color-fg-muted)] hover:bg-[var(--color-bg-elev-2)] hover:text-[var(--color-fg)]',
    danger:
      'bg-[var(--color-danger)]/15 text-[var(--color-danger)] hover:bg-[var(--color-danger)]/25'
  };

  const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base'
  };
</script>

<button class={cn(base, variants[variant], sizes[size], klass)} {...rest}>
  {#if children}{@render children()}{/if}
</button>
