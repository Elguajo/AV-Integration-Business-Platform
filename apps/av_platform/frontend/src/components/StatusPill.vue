<script setup lang="ts">
// Project state as a solid pill (UI-03). The colour repeats the text; it is never the only signal.
import type { ProjectStatus } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'

defineProps<{ status: ProjectStatus }>()

const STYLE: Record<ProjectStatus, string> = {
  problem: 'bg-surface-red-2 text-ink-red-6',
  risk: 'bg-surface-amber-2 text-ink-amber-8',
  unknown: 'bg-surface-gray-3 text-ink-gray-7',
  on_plan: 'bg-surface-green-2 text-ink-green-6',
}
</script>

<template>
  <span class="inline-flex items-center whitespace-nowrap rounded-3 px-2 py-0.5 text-p-xs font-medium" :class="STYLE[status]">
    {{ t.status[status] }}
  </span>
</template>
