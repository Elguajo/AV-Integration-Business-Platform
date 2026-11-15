<script setup lang="ts">
// Record template (UI-03, research/12 §6.2а): a full-height column of sections, then the record
// header, the main area and a side panel. No frame around the record: it is the page itself.
// The grouping tree of D-Tools waits for rooms and systems (UI-04). Below lg the column becomes a
// row of sections and the side panel moves under the main area.
export interface RecordSection {
  key: string
  label: string
  icon: string
  count?: number | null
}

defineProps<{ sections: RecordSection[]; sectionsLabel: string }>()
const active = defineModel<string>('active', { required: true })
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-surface-base lg:flex-row">
    <nav
      class="flex shrink-0 gap-0.5 overflow-x-auto border-b border-outline-gray-2 px-2 py-1.5 lg:w-52 lg:flex-col lg:overflow-y-auto lg:border-b-0 lg:border-r lg:px-2 lg:py-3"
      :aria-label="sectionsLabel"
    >
      <slot name="nav-top" />
      <button
        v-for="section in sections"
        :key="section.key"
        type="button"
        class="flex h-8 shrink-0 items-center gap-2.5 whitespace-nowrap rounded-4 px-2 text-p-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
        :class="active === section.key ? 'bg-surface-gray-3 font-medium text-ink-gray-9' : 'text-ink-gray-7 hover:bg-surface-gray-2'"
        :aria-current="active === section.key ? 'page' : undefined"
        @click="active = section.key"
      >
        <span :class="section.icon" class="size-4 shrink-0" aria-hidden="true" />
        <span class="lg:flex-1 lg:text-left">{{ section.label }}</span>
        <span v-if="section.count" class="tabular-nums text-p-xs text-ink-gray-5">{{ section.count }}</span>
      </button>
    </nav>

    <div class="min-h-0 min-w-0 flex-1 overflow-y-auto">
      <div class="flex min-h-full flex-col">
        <header class="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-outline-gray-2 px-4 py-3 sm:px-5">
          <slot name="header" />
        </header>
        <div class="grid flex-1 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_280px]">
          <main class="min-w-0 space-y-4 p-4 sm:p-5">
            <slot />
          </main>
          <aside class="space-y-5 border-t border-outline-gray-2 bg-surface-gray-1 p-4 text-p-sm xl:border-l xl:border-t-0">
            <slot name="aside" />
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>
