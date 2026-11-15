<script setup lang="ts">
// Shell of the role screens (ADR-006): one app sidebar with the screens and a global header
// (UI-05); each screen owns the rest. On a phone the sidebar slides out from the header. Desk is
// one link away in the header for ERPNext and administration.
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar, Dropdown, FrappeUIProvider } from 'frappe-ui'
import { boot } from './boot'
import HeaderNotifications from './components/HeaderNotifications.vue'
import HeaderSearch from './components/HeaderSearch.vue'
import { VIEW_ICONS, ruShell as t } from './i18n/shell'

const COLLAPSED_KEY = 'av-shell-collapsed'
const RECORD_EXPANDED_KEY = 'av-shell-record-expanded'

const route = useRoute()
// Two remembered choices: the menu width on ordinary screens, and on record pages, where the menu
// folds to icons by default and stays open only if the user opened it there.
const collapsed = ref(readFlag(COLLAPSED_KEY))
const recordExpanded = ref(readFlag(RECORD_EXPANDED_KEY))
const onRecord = computed(() => route.meta.record === true)
const narrow = computed(() => (onRecord.value ? !recordExpanded.value : collapsed.value))
const drawer = ref(false)

const items = computed(() =>
  boot.views.map((view) => ({ view, to: `/${view}`, label: t.views[view], icon: VIEW_ICONS[view] })),
)
const title = computed(() => (route.meta.view ? t.views[route.meta.view] : t.app))
// «+» opens a new document in Desk; the server lists only what the user may create (UI-05).
const createMenu = boot.create.map((option) => ({
  label: t.create.doctypes[option.doctype] ?? option.doctype,
  icon: 'lucide-plus',
  onClick: () => window.location.assign(option.href),
}))
const userMenu = [
  {
    group: boot.full_name || boot.user,
    options: [
      ...(boot.desk
        ? [{ label: t.desk, icon: 'lucide-layout-grid', onClick: () => window.location.assign('/desk') }]
        : []),
      { label: t.logout, icon: 'lucide-log-out', onClick: logout },
    ],
  },
]

watch(() => route.fullPath, () => (drawer.value = false))
watch(collapsed, (value) => writeFlag(COLLAPSED_KEY, value))
watch(recordExpanded, (value) => writeFlag(RECORD_EXPANDED_KEY, value))

function setNarrow(value: boolean) {
  if (onRecord.value) recordExpanded.value = !value
  else collapsed.value = value
}

function readFlag(key: string) {
  try {
    return localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

function writeFlag(key: string, value: boolean) {
  try {
    localStorage.setItem(key, value ? '1' : '0')
  } catch {
    // Storage may be unavailable; the choice then lasts until reload.
  }
}

async function logout() {
  await fetch('/api/method/logout', {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': window.csrf_token ?? '' },
  })
  window.location.href = '/login'
}
</script>

<template>
  <FrappeUIProvider>
    <div class="flex h-dvh w-full overflow-hidden bg-surface-base text-ink-gray-8">
      <div v-if="drawer" class="fixed inset-0 z-30 bg-black/30 md:hidden" aria-hidden="true" @click="drawer = false" />
      <aside
        class="z-40 flex shrink-0 flex-col border-r border-outline-gray-2 bg-surface-sidebar max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:w-64 max-md:shadow-xl max-md:transition-transform"
        :class="[narrow ? 'md:w-14' : 'md:w-56', drawer ? 'max-md:translate-x-0' : 'max-md:-translate-x-full']"
        :aria-label="t.menu"
      >
        <div class="flex h-12 items-center gap-2 px-3">
          <span class="grid size-8 shrink-0 place-items-center rounded-5 bg-surface-gray-7 text-p-sm font-semibold text-ink-gray-1">AV</span>
          <span v-if="!narrow || drawer" class="min-w-0 flex-1 truncate text-p-base font-semibold text-ink-gray-9">{{ t.app }}</span>
          <button
            v-if="!narrow"
            type="button"
            class="ml-auto grid size-7 place-items-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-3 max-md:hidden"
            :aria-label="t.collapse"
            :title="t.collapse"
            @click="setNarrow(true)"
          >
            <span class="lucide-panel-left-close size-4" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="ml-auto grid size-7 place-items-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-3 md:hidden"
            :aria-label="t.closeMenu"
            @click="drawer = false"
          >
            <span class="lucide-x size-4" aria-hidden="true" />
          </button>
        </div>
        <button
          v-if="narrow"
          type="button"
          class="mx-auto mb-1 grid size-8 place-items-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-3 max-md:hidden"
          :aria-label="t.expand"
          :title="t.expand"
          @click="setNarrow(false)"
        >
          <span class="lucide-panel-left-open size-4" aria-hidden="true" />
        </button>

        <nav class="flex flex-col gap-0.5 px-2 py-1">
          <RouterLink
            v-for="item in items"
            :key="item.view"
            :to="item.to"
            class="flex h-8 items-center gap-2.5 rounded-4 px-2 text-p-sm"
            :class="route.meta.view === item.view ? 'bg-surface-base font-medium text-ink-gray-9 shadow-sm' : 'text-ink-gray-7 hover:bg-surface-gray-3'"
            :aria-current="route.meta.view === item.view ? 'page' : undefined"
            :title="narrow ? item.label : undefined"
          >
            <span :class="item.icon" class="size-4 shrink-0" aria-hidden="true" />
            <span :class="narrow ? 'md:sr-only' : ''" class="truncate">{{ item.label }}</span>
          </RouterLink>
        </nav>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <!-- Global header (UI-05), as in D-Tools Cloud: where I am on the left; search, «+»,
             notifications, Desk and the user menu on the right, the same on every screen.
             Page actions stay in each screen's own toolbar (research/12 §6.2в). -->
        <header class="flex h-12 shrink-0 items-center gap-1.5 border-b border-outline-gray-2 px-3 sm:gap-2 sm:px-5">
          <button
            type="button"
            class="grid size-8 shrink-0 place-items-center rounded-4 text-ink-gray-7 hover:bg-surface-gray-2 md:hidden"
            :aria-label="t.openMenu"
            :aria-expanded="drawer"
            @click="drawer = true"
          >
            <span class="lucide-menu size-5" aria-hidden="true" />
          </button>
          <!-- On a record page the way back is in the record's column of sections (UI-03). -->
          <h1 class="min-w-0 truncate text-lg font-semibold text-ink-gray-9">{{ title }}</h1>
          <span class="grow" />

          <HeaderSearch />
          <Dropdown v-if="createMenu.length" :options="createMenu" align="end">
            <template #default>
              <button
                type="button"
                class="grid size-8 shrink-0 place-items-center rounded-4 bg-surface-gray-7 text-ink-gray-1 hover:bg-surface-gray-6"
                :aria-label="t.create.button"
                :title="t.create.button"
              >
                <span class="lucide-plus size-4" aria-hidden="true" />
              </button>
            </template>
          </Dropdown>
          <HeaderNotifications />
          <a
            v-if="boot.desk"
            href="/desk"
            class="grid size-8 shrink-0 place-items-center rounded-4 text-ink-gray-7 hover:bg-surface-gray-3 max-sm:hidden"
            :aria-label="t.desk"
            :title="`${t.desk}: ${t.deskHint}`"
          >
            <span class="lucide-layout-grid size-4" aria-hidden="true" />
          </a>
          <Dropdown :options="userMenu" align="end">
            <template #default>
              <button
                type="button"
                class="grid size-8 shrink-0 place-items-center rounded-full hover:ring-2 hover:ring-outline-gray-2"
                :aria-label="t.userMenu"
                :title="boot.full_name"
              >
                <Avatar :image="boot.image ?? undefined" :label="boot.full_name || boot.user" size="md" />
              </button>
            </template>
          </Dropdown>
        </header>
        <main class="min-h-0 flex-1">
          <RouterView />
        </main>
      </div>
    </div>
  </FrappeUIProvider>
</template>
