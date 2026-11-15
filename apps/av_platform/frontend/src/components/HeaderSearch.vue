<script setup lang="ts">
// Global search of the header (UI-05): Ctrl+K or ⌘K opens one box for screens, «create» actions
// and records (projects, works, proposals, clients). Records come from the server, which keeps only what
// the user may read; the box never shows a record the user could not open.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Dialog } from 'frappe-ui'
import { boot } from '../boot'
import { VIEW_ICONS, ruShell as t } from '../i18n/shell'
import { follow, searchRecords, type SearchResult } from '../shellApi'

interface Item {
  id: string
  group: string
  label: string
  detail: string | null
  icon: string
  href: string
}

const RECORD_ICONS: Record<string, string> = {
  Project: 'lucide-folder-kanban',
  Task: 'lucide-square-check',
  Quotation: 'lucide-file-text',
  Customer: 'lucide-building-2',
}
const MIN_CHARS = 2
const DEBOUNCE_MS = 250

const open = ref(false)
const text = ref('')
const results = ref<SearchResult[]>([])
const state = ref<'idle' | 'loading' | 'done' | 'error'>('idle')
const active = ref(0)
const listEl = ref<HTMLElement | null>(null)
const isMac = /Mac|iPhone|iPad/.test(navigator.platform)
const shortcut = isMac ? '⌘K' : 'Ctrl K'
let timer: ReturnType<typeof setTimeout> | undefined
let sequence = 0

const query = computed(() => text.value.trim())
const matches = (label: string) => !query.value || label.toLowerCase().includes(query.value.toLowerCase())

const items = computed<Item[]>(() => [
  ...boot.views
    .filter((view) => matches(t.views[view]))
    .map((view) => ({
      id: `view-${view}`,
      group: t.search.screens,
      label: t.views[view],
      detail: null,
      icon: VIEW_ICONS[view],
      href: `/av/${view}`,
    })),
  ...boot.create
    .filter((option) => matches(`${t.create.button} ${t.create.doctypes[option.doctype] ?? option.doctype}`))
    .map((option) => ({
      id: `create-${option.doctype}`,
      group: t.search.create,
      label: t.create.doctypes[option.doctype] ?? option.doctype,
      detail: t.create.hint,
      icon: 'lucide-plus',
      href: option.href,
    })),
  ...results.value.map((row) => ({
    id: `record-${row.doctype}-${row.name}`,
    group: t.search.doctypes[row.doctype] ?? row.doctype,
    label: row.title,
    detail: [row.name !== row.title ? row.name : null, row.subtitle].filter(Boolean).join(' · ') || null,
    icon: RECORD_ICONS[row.doctype] ?? 'lucide-file',
    href: row.href,
  })),
])

const groups = computed(() => {
  const byGroup = new Map<string, { item: Item; index: number }[]>()
  items.value.forEach((item, index) => {
    const list = byGroup.get(item.group) ?? []
    list.push({ item, index })
    byGroup.set(item.group, list)
  })
  return [...byGroup.entries()].map(([label, entries]) => ({ label, entries }))
})

const activeId = computed(() => (items.value[active.value] ? `av-search-${items.value[active.value].id}` : undefined))

watch(query, (value) => {
  clearTimeout(timer)
  active.value = 0
  sequence += 1
  if (value.length < MIN_CHARS) {
    results.value = []
    state.value = 'idle'
    return
  }
  state.value = 'loading'
  const current = sequence
  timer = setTimeout(async () => {
    try {
      const rows = await searchRecords(value)
      if (current !== sequence) return
      results.value = rows
      state.value = 'done'
    } catch {
      if (current !== sequence) return
      results.value = []
      state.value = 'error'
    }
  }, DEBOUNCE_MS)
})

watch(items, () => {
  if (active.value >= items.value.length) active.value = Math.max(items.value.length - 1, 0)
})

watch(open, (value) => {
  if (value) return
  clearTimeout(timer)
  sequence += 1
  text.value = ''
  results.value = []
  state.value = 'idle'
})

function move(step: number) {
  if (!items.value.length) return
  active.value = (active.value + step + items.value.length) % items.value.length
  listEl.value?.querySelector(`#${CSS.escape(activeId.value ?? '')}`)?.scrollIntoView({ block: 'nearest' })
}

function choose(event: MouseEvent | KeyboardEvent, item: Item | undefined) {
  if (!item) return
  follow(event, item.href)
  if (!event.defaultPrevented) return
  open.value = false
}

function onKey(event: KeyboardEvent) {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    move(1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    move(-1)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    choose(event, items.value[active.value])
  }
}

function onShortcut(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    open.value = !open.value
  }
}

onMounted(() => window.addEventListener('keydown', onShortcut))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onShortcut)
  clearTimeout(timer)
})
</script>

<template>
  <button
    type="button"
    class="flex h-8 items-center gap-2 rounded-4 text-p-sm text-ink-gray-6 hover:bg-surface-gray-3 max-sm:w-8 max-sm:justify-center sm:w-56 sm:border sm:border-outline-gray-2 sm:bg-surface-gray-1 sm:px-2.5"
    :aria-label="t.search.button"
    :aria-keyshortcuts="isMac ? 'Meta+K' : 'Control+K'"
    :title="`${t.search.button} (${shortcut})`"
    @click="open = true"
  >
    <span class="lucide-search size-4 shrink-0" aria-hidden="true" />
    <span class="flex-1 text-left max-sm:hidden">{{ t.search.button }}</span>
    <kbd class="rounded-3 border border-outline-gray-2 px-1 font-sans text-p-xs text-ink-gray-5 max-sm:hidden">{{ shortcut }}</kbd>
  </button>

  <Dialog v-model:open="open" bare position="top" size="xl">
    <div class="flex max-h-[min(32rem,75dvh)] flex-col">
      <Dialog.Title class="sr-only">{{ t.search.title }}</Dialog.Title>
      <div class="flex items-center gap-2 border-b border-outline-gray-2 px-4">
        <span class="lucide-search size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <input
          v-model="text"
          autofocus
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-controls="av-search-list"
          :aria-expanded="items.length > 0"
          :aria-activedescendant="activeId"
          :placeholder="t.search.placeholder"
          class="h-12 min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-9 placeholder:text-ink-gray-4 focus:ring-0"
          @keydown="onKey"
        />
        <span v-if="state === 'loading'" class="text-p-xs text-ink-gray-5" role="status">{{ t.search.loading }}</span>
      </div>

      <div id="av-search-list" ref="listEl" role="listbox" :aria-label="t.search.title" class="min-h-0 flex-1 overflow-y-auto p-2">
        <div v-for="group in groups" :key="group.label" role="group" :aria-label="group.label" class="mb-1">
          <div class="px-2 pb-1 pt-2 text-p-xs font-medium text-ink-gray-5" aria-hidden="true">{{ group.label }}</div>
          <a
            v-for="{ item, index } in group.entries"
            :id="`av-search-${item.id}`"
            :key="item.id"
            :href="item.href"
            role="option"
            tabindex="-1"
            :aria-selected="index === active"
            class="flex min-h-9 items-center gap-2.5 rounded-4 px-2 py-1.5 text-p-sm"
            :class="index === active ? 'bg-surface-gray-3 text-ink-gray-9' : 'text-ink-gray-8'"
            @mousemove="active = index"
            @click="choose($event, item)"
          >
            <span :class="item.icon" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
            <span class="min-w-0 flex-1 truncate">{{ item.label }}</span>
            <span v-if="item.detail" class="max-w-[45%] shrink-0 truncate text-p-xs text-ink-gray-5">{{ item.detail }}</span>
          </a>
        </div>
        <p v-if="query.length > 0 && query.length < MIN_CHARS" class="px-2 py-3 text-p-sm text-ink-gray-5">{{ t.search.short }}</p>
        <p v-else-if="state === 'done' && !results.length" class="px-2 py-3 text-p-sm text-ink-gray-5">{{ t.search.none(query) }}</p>
        <p v-else-if="state === 'error'" class="px-2 py-3 text-p-sm text-ink-red-6" role="alert">{{ t.search.error }}</p>
      </div>

      <div class="border-t border-outline-gray-2 px-4 py-2 text-p-xs text-ink-gray-5 max-sm:hidden">{{ t.search.hints }}</div>
    </div>
  </Dialog>
</template>
