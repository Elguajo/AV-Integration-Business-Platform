<script setup lang="ts">
// A count meter "done of total" (UI-06). Shows the counts, never a percentage (OVW-02); with no
// plan (total 0) the ring stays empty and says so instead of showing 0 or 100.
import { computed } from 'vue'

const props = defineProps<{ done: number; total: number; label: string; empty: string }>()

const R = 16
const LENGTH = 2 * Math.PI * R
const dash = computed(() => (props.total ? (Math.min(props.done, props.total) / props.total) * LENGTH : 0))
</script>

<template>
  <div class="flex min-w-0 items-center gap-3">
    <svg viewBox="0 0 40 40" class="size-14 shrink-0 -rotate-90" aria-hidden="true">
      <circle cx="20" cy="20" :r="R" fill="none" stroke-width="4" style="stroke: var(--surface-gray-3)" />
      <circle
        v-if="dash"
        cx="20"
        cy="20"
        :r="R"
        fill="none"
        stroke-width="4"
        stroke-linecap="round"
        :stroke-dasharray="`${dash} ${LENGTH}`"
        style="stroke: var(--ink-blue-5)"
      />
    </svg>
    <div class="min-w-0">
      <p v-if="total" class="text-xl font-semibold tabular-nums text-ink-gray-9">
        {{ done }}<span class="text-p-base font-normal text-ink-gray-5"> / {{ total }}</span>
      </p>
      <p v-else class="text-p-sm text-ink-gray-5">{{ empty }}</p>
      <p class="text-p-sm text-ink-gray-6">{{ label }}</p>
    </div>
  </div>
</template>
