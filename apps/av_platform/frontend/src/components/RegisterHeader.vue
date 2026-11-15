<script setup lang="ts">
// Register template (UI-03, research/12 §6.2а): view switch, search, «Все / Мои», filter pills and
// one primary action on the right. Pages pass their own filters through the default slot.
import { Button, TextInput } from 'frappe-ui'

export type RegisterView = 'list' | 'kanban'

defineProps<{
  searchPlaceholder: string
  mineLabel: string
  allLabel: string
  scopeLabel: string
  listLabel: string
  kanbanLabel: string
  actionLabel?: string
  actionHref?: string
}>()

const view = defineModel<RegisterView>('view', { required: true })
const search = defineModel<string>('search', { required: true })
const mine = defineModel<boolean>('mine', { required: true })
</script>

<template>
  <div class="space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="inline-flex rounded-4 bg-surface-gray-2 p-0.5" role="group">
        <Button
          :variant="view === 'list' ? 'outline' : 'ghost'"
          icon="lucide-list"
          :tooltip="listLabel"
          :aria-label="listLabel"
          :aria-pressed="view === 'list'"
          @click="view = 'list'"
        />
        <Button
          :variant="view === 'kanban' ? 'outline' : 'ghost'"
          icon="lucide-square-kanban"
          :tooltip="kanbanLabel"
          :aria-label="kanbanLabel"
          :aria-pressed="view === 'kanban'"
          @click="view = 'kanban'"
        />
      </div>
      <TextInput v-model="search" type="search" :placeholder="searchPlaceholder" class="w-full min-w-0 sm:w-72">
        <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
      </TextInput>
      <span class="grow" />
      <a v-if="actionLabel && actionHref" :href="actionHref">
        <Button variant="solid" icon-left="lucide-plus" :label="actionLabel" />
      </a>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <div class="inline-flex rounded-4 bg-surface-gray-2 p-0.5 text-p-sm" role="group" :aria-label="scopeLabel">
        <button
          type="button"
          class="rounded-3 px-3 py-1"
          :class="!mine ? 'bg-surface-white font-medium text-ink-gray-9 shadow-sm' : 'text-ink-gray-6'"
          :aria-pressed="!mine"
          @click="mine = false"
        >
          {{ allLabel }}
        </button>
        <button
          type="button"
          class="rounded-3 px-3 py-1"
          :class="mine ? 'bg-surface-white font-medium text-ink-gray-9 shadow-sm' : 'text-ink-gray-6'"
          :aria-pressed="mine"
          @click="mine = true"
        >
          {{ mineLabel }}
        </button>
      </div>
      <slot />
    </div>
  </div>
</template>
