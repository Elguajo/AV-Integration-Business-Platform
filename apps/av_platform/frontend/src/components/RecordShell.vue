<script setup lang="ts">
// Record template (UI-03, research/12 §6.2а): record header, a narrow rail of sections, a tree of
// groupings, the main area and a side panel. On a phone the rail becomes a row and the tree and
// side panel move under the main area.
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
  <div class="overflow-hidden rounded-6 border border-outline-gray-2 bg-surface-white">
    <header class="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-outline-gray-2 px-4 py-3">
      <slot name="header" />
    </header>
    <div class="grid grid-cols-1 md:grid-cols-[72px_minmax(0,1fr)] xl:grid-cols-[72px_190px_minmax(0,1fr)] 2xl:grid-cols-[72px_190px_minmax(0,1fr)_240px]">
      <nav
        class="flex overflow-x-auto border-b border-outline-gray-2 bg-surface-gray-1 md:flex-col md:border-b-0 md:border-r"
        :aria-label="sectionsLabel"
      >
        <button
          v-for="section in sections"
          :key="section.key"
          type="button"
          class="flex min-w-[72px] flex-col items-center gap-1 px-1 py-2.5 text-[11px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-outline-gray-4"
          :class="active === section.key ? 'bg-surface-blue-2 font-medium text-ink-blue-6' : 'text-ink-gray-6 hover:bg-surface-gray-2'"
          :aria-current="active === section.key ? 'page' : undefined"
          @click="active = section.key"
        >
          <span :class="section.icon" class="size-[18px]" aria-hidden="true" />
          <span>{{ section.label }}<template v-if="section.count"> · {{ section.count }}</template></span>
        </button>
      </nav>
      <aside class="border-r border-outline-gray-2 p-3 max-xl:hidden">
        <slot name="tree" />
      </aside>
      <main class="min-w-0 space-y-4 p-4">
        <slot />
      </main>
      <aside class="space-y-5 border-t border-outline-gray-2 bg-surface-gray-1 p-4 text-p-sm md:col-span-2 xl:col-span-3 2xl:col-span-1 2xl:border-l 2xl:border-t-0">
        <slot name="aside" />
      </aside>
    </div>
  </div>
</template>
