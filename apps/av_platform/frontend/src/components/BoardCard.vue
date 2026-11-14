<script setup lang="ts">
import { computed } from 'vue'
import { Dropdown } from 'frappe-ui'
import type { BoardStage, BoardTask } from '../pmApi'
import { ruPm } from '../i18n/pm'
import { date } from '../format'

const props = defineProps<{
  task: BoardTask
  stages: BoardStage[]
  projectName: string | null
  canMove: boolean
  saving: boolean
}>()
const emit = defineEmits<{ move: [stage: string] }>()

const place = computed(() => [props.task.room, props.task.system].filter(Boolean).join(' · '))
const assignees = computed(() =>
  props.task.assignees.map((a) => a.full_name || a.name).join(', '),
)
const moveOptions = computed(() =>
  props.stages
    .filter((s) => s.name !== props.task.stage)
    .map((s) => ({ label: s.label, onClick: () => emit('move', s.name) })),
)

function onDragStart(event: DragEvent) {
  if (!event.dataTransfer) return
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', props.task.name)
}
</script>

<template>
  <article
    class="rounded-6 border bg-surface-elevation-1 p-3 transition-colors"
    :class="[
      task.block_reason ? 'border-outline-amber-2' : 'border-outline-gray-1',
      saving ? 'opacity-60' : 'hover:border-outline-gray-3',
      canMove && !saving ? 'cursor-grab' : '',
    ]"
    :draggable="canMove && !saving"
    :aria-busy="saving"
    @dragstart="onDragStart"
  >
    <div class="flex items-start justify-between gap-2">
      <a
        :href="`/app/task/${encodeURIComponent(task.name)}`"
        target="_blank"
        rel="noopener"
        class="min-w-0 text-base-medium text-ink-gray-9 hover:underline"
        :title="ruPm.card.open"
      >
        <span v-if="task.is_milestone" class="lucide-flag mr-1 inline-block size-3.5 align-[-2px] text-ink-gray-5" :aria-label="ruPm.card.milestone" />
        {{ task.subject }}
      </a>
      <Dropdown
        v-if="canMove"
        :options="moveOptions"
        align="end"
        class="shrink-0"
        :button="{
          icon: 'lucide-arrow-right-left',
          variant: 'ghost',
          size: 'sm',
          tooltip: ruPm.card.moveTo,
          disabled: saving,
        }"
        :aria-label="`${ruPm.card.move}: ${task.subject}`"
      />
    </div>

    <div v-if="projectName" class="mt-1 truncate text-sm text-ink-gray-5">{{ projectName }}</div>
    <div v-if="place" class="mt-1.5 flex items-center gap-1.5 text-sm text-ink-gray-6">
      <span class="lucide-map-pin size-3.5 shrink-0" aria-hidden="true" />
      <span class="truncate">{{ place }}</span>
    </div>

    <div class="mt-2 flex items-center justify-between gap-2 text-sm">
      <span class="flex min-w-0 items-center gap-1.5 text-ink-gray-6">
        <span class="lucide-user size-3.5 shrink-0" aria-hidden="true" />
        <span class="truncate">{{ assignees || ruPm.card.noAssignee }}</span>
      </span>
      <span
        class="shrink-0 tabular-nums"
        :class="task.is_overdue ? 'font-medium text-ink-red-4' : 'text-ink-gray-5'"
        :title="task.is_overdue ? ruPm.card.overdue : undefined"
      >
        {{ task.end ? date(task.end) : ruPm.card.noDate }}
      </span>
    </div>

    <div
      v-if="task.block_reason"
      class="mt-2 rounded-4 bg-surface-amber-2 px-2 py-1 text-p-xs text-ink-amber-7"
    >
      <span class="font-medium">{{ ruPm.card.blocked }}:</span> {{ task.block_reason }}
    </div>
    <div v-if="saving" class="mt-2 text-p-xs text-ink-gray-5">{{ ruPm.card.saving }}</div>
  </article>
</template>
