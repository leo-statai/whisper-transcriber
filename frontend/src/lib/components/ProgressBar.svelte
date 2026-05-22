<script lang="ts">
  interface Props {
    value: number; // 0-100
    indeterminate?: boolean;
    label?: string;
  }
  let { value, indeterminate = false, label }: Props = $props();
  const pct = $derived(Math.max(0, Math.min(100, value)));
</script>

<div class="w-full">
  {#if label}
    <div class="flex justify-between text-xs text-[var(--color-fg-muted)] mb-1.5">
      <span>{label}</span>
      {#if !indeterminate}<span class="tabular-nums">{pct.toFixed(1)}%</span>{/if}
    </div>
  {/if}
  <div
    class="h-2 w-full rounded-full bg-[var(--color-bg-elev-2)] overflow-hidden"
    role="progressbar"
    aria-valuemin="0"
    aria-valuemax="100"
    aria-valuenow={indeterminate ? undefined : pct}
  >
    {#if indeterminate}
      <div
        class="h-full w-1/3 bg-[var(--color-accent)] rounded-full"
        style="animation: progress-indeterminate 1.5s ease-in-out infinite;"
      ></div>
    {:else}
      <div
        class="h-full bg-[var(--color-accent)] rounded-full transition-[width] duration-300"
        style="width: {pct}%"
      ></div>
    {/if}
  </div>
</div>

<style>
  @keyframes progress-indeterminate {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
  }
</style>
