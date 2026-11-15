<script setup lang="ts">
// Shell of the role screens (ADR-006): one app sidebar and a header; each screen owns the rest.
// On a phone the sidebar slides out from the header. Desk is one link away for ERPNext and
// administration.
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Dropdown, FrappeUIProvider } from 'frappe-ui'
import { boot } from './boot'
import { VIEW_ICONS, ruShell as t } from './i18n/shell'

const COLLAPSED_KEY = 'av-shell-collapsed'

const route = useRoute()
const collapsed = ref(readCollapsed())
const drawer = ref(false)

const items = computed(() =>
  boot.views.map((view) => ({ view, to: `/${view}`, label: t.views[view], icon: VIEW_ICONS[view] })),
)
const title = computed(() => (route.meta.view ? t.views[route.meta.view] : t.app))
const initials = computed(() =>
  (boot.full_name || boot.user)
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join(''),
)
const userMenu = [{ label: t.logout, icon: 'lucide-log-out', onClick: logout }]

watch(() => route.fullPath, () => (drawer.value = false))
watch(collapsed, (value) => {
  try {
    localStorage.setItem(COLLAPSED_KEY, value ? '1' : '0')
  } catch {
    // Storage may be unavailable; the choice then lasts until reload.
  }
})

function readCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1'
  } catch {
    return false
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
        :class="[collapsed ? 'md:w-14' : 'md:w-56', drawer ? 'max-md:translate-x-0' : 'max-md:-translate-x-full']"
        :aria-label="t.menu"
      >
        <div class="flex h-12 items-center gap-2 px-3">
          <span class="grid size-8 shrink-0 place-items-center rounded-5 bg-surface-gray-7 text-p-sm font-semibold text-ink-gray-1">AV</span>
          <span v-if="!collapsed || drawer" class="min-w-0 flex-1 truncate text-p-base font-semibold text-ink-gray-9">{{ t.app }}</span>
          <button
            v-if="!collapsed"
            type="button"
            class="ml-auto grid size-7 place-items-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-3 max-md:hidden"
            :aria-label="t.collapse"
            :title="t.collapse"
            @click="collapsed = true"
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
          v-if="collapsed"
          type="button"
          class="mx-auto mb-1 grid size-8 place-items-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-3 max-md:hidden"
          :aria-label="t.expand"
          :title="t.expand"
          @click="collapsed = false"
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
            :title="collapsed ? item.label : undefined"
          >
            <span :class="item.icon" class="size-4 shrink-0" aria-hidden="true" />
            <span :class="collapsed ? 'md:sr-only' : ''" class="truncate">{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="mt-auto flex flex-col gap-0.5 border-t border-outline-gray-2 px-2 py-2">
          <a
            v-if="boot.desk"
            href="/desk"
            class="flex h-8 items-center gap-2.5 rounded-4 px-2 text-p-sm text-ink-gray-7 hover:bg-surface-gray-3"
            :title="t.deskHint"
          >
            <span class="lucide-layout-grid size-4 shrink-0" aria-hidden="true" />
            <span :class="collapsed ? 'md:sr-only' : ''" class="truncate">{{ t.desk }}</span>
          </a>
          <Dropdown :options="userMenu" placement="right">
            <template #default>
              <button
                type="button"
                class="flex h-9 w-full items-center gap-2.5 rounded-4 px-1.5 text-left text-p-sm text-ink-gray-8 hover:bg-surface-gray-3"
                :title="collapsed ? boot.full_name : undefined"
              >
                <span class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-4 text-[10px] font-semibold text-ink-gray-8">{{ initials }}</span>
                <span :class="collapsed ? 'md:sr-only' : ''" class="truncate">{{ boot.full_name }}</span>
              </button>
            </template>
          </Dropdown>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="flex h-12 shrink-0 items-center gap-2 border-b border-outline-gray-2 px-3 sm:px-5">
          <button
            type="button"
            class="grid size-8 place-items-center rounded-4 text-ink-gray-7 hover:bg-surface-gray-2 md:hidden"
            :aria-label="t.openMenu"
            :aria-expanded="drawer"
            @click="drawer = true"
          >
            <span class="lucide-menu size-5" aria-hidden="true" />
          </button>
          <h1 class="truncate text-lg font-semibold text-ink-gray-9">{{ title }}</h1>
        </header>
        <main class="min-h-0 flex-1">
          <RouterView />
        </main>
      </div>
    </div>
  </FrappeUIProvider>
</template>
