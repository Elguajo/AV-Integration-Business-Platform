<script setup lang="ts">
// Five direction marks of a project row (UI-03, OVW-01/02). Only works are tracked today; the other
// directions are grey and say «учёт не ведётся» — unknown is never shown as zero or as green.
// Each mark names its direction and state in its own title and aria-label.
import { computed } from 'vue'
import type { ProjectStatus } from '../overviewApi'
import { ruOverview as t } from '../i18n/overview'

const props = defineProps<{ works: ProjectStatus }>()

const COLOR: Record<ProjectStatus, string> = {
  problem: 'bg-surface-red-5',
  risk: 'bg-surface-amber-5',
  unknown: 'bg-surface-gray-4',
  on_plan: 'bg-surface-green-3',
}

const marks = computed(() => [
  { label: t.directions.works, value: t.directions.states[props.works], color: COLOR[props.works] },
  ...(['procurement', 'install', 'tests', 'money'] as const).map((key) => ({
    label: t.directions[key],
    value: t.directions.untrackedState,
    color: 'bg-surface-gray-3',
  })),
])
</script>

<template>
  <span class="inline-flex gap-[3px]" role="group" :aria-label="t.table.directions">
    <i
      v-for="mark in marks"
      :key="mark.label"
      class="block size-3 rounded-[3px]"
      :class="mark.color"
      role="img"
      :aria-label="`${mark.label}: ${mark.value}`"
      :title="`${mark.label}: ${mark.value}`"
    />
  </span>
</template>
