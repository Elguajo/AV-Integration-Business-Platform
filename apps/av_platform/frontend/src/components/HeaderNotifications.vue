<script setup lang="ts">
// Notifications of the header (UI-05): Frappe's own Notification Log, the one place notifications
// are kept (assignments, mentions, shares). The bell shows only what was sent to this user; marking
// as read goes through Frappe's methods, which touch the user's own logs only.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Button, Popover } from 'frappe-ui'
import { ruShell as t } from '../i18n/shell'
import { follow, loadNotifications, markAllRead, markRead, type NotificationItem } from '../shellApi'

const REFRESH_MS = 120_000

const items = ref<NotificationItem[]>([])
const unread = ref(0)
const failed = ref(false)
const loading = ref(false)
let timer: ReturnType<typeof setInterval> | undefined

const badge = computed(() => (unread.value > 99 ? '99+' : String(unread.value)))
const when = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

async function refresh() {
  if (loading.value) return
  loading.value = true
  try {
    const data = await loadNotifications()
    items.value = data.items
    unread.value = data.unread
    failed.value = false
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

async function readAll() {
  try {
    await markAllRead()
  } finally {
    await refresh()
  }
}

async function openItem(event: MouseEvent, item: NotificationItem, close: () => void) {
  if (item.href) follow(event, item.href)
  else event.preventDefault()
  if (!item.read) {
    item.read = true
    unread.value = Math.max(unread.value - 1, 0)
    // A lost mark only leaves the item unread; the next refresh shows the server's state.
    markRead(item.name).catch(() => undefined)
  }
  if (event.defaultPrevented) close()
}

function onVisible() {
  if (document.visibilityState === 'visible') refresh()
}

onMounted(() => {
  refresh()
  timer = setInterval(() => document.visibilityState === 'visible' && refresh(), REFRESH_MS)
  document.addEventListener('visibilitychange', onVisible)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisible)
})
</script>

<template>
  <Popover side="bottom" align="end" @open="refresh">
    <template #trigger>
      <button
        type="button"
        class="relative grid size-8 place-items-center rounded-4 text-ink-gray-7 hover:bg-surface-gray-3"
        :aria-label="unread ? t.notifications.unread(unread) : t.notifications.button"
        :title="t.notifications.button"
      >
        <span class="lucide-bell size-4" aria-hidden="true" />
        <span
          v-if="unread"
          class="absolute -right-0.5 -top-0.5 min-w-4 rounded-full bg-surface-red-6 px-1 text-center text-[10px] font-semibold leading-4 text-ink-gray-1"
          aria-hidden="true"
        >{{ badge }}</span>
      </button>
    </template>
    <template #default="{ close }">
      <div class="flex w-[min(22rem,calc(100vw-2rem))] flex-col">
        <div class="flex items-center justify-between gap-2 border-b border-outline-gray-2 px-3 py-2">
          <span class="text-p-sm font-semibold text-ink-gray-9">{{ t.notifications.title }}</span>
          <Button v-if="unread" variant="ghost" size="sm" :label="t.notifications.markAll" @click="readAll" />
        </div>
        <div class="max-h-96 overflow-y-auto p-1">
          <div v-if="failed" class="flex items-center justify-between gap-2 px-2 py-3 text-p-sm text-ink-red-6" role="alert">
            {{ t.notifications.error }}
            <Button size="sm" :label="t.notifications.retry" @click="refresh" />
          </div>
          <p v-else-if="!items.length" class="px-2 py-6 text-center text-p-sm text-ink-gray-5">{{ t.notifications.empty }}</p>
          <a
            v-for="item in items"
            v-else
            :key="item.name"
            :href="item.href ?? undefined"
            class="flex gap-2 rounded-4 px-2 py-2 text-p-sm hover:bg-surface-gray-2"
            :class="item.href ? 'cursor-pointer' : 'cursor-default'"
            @click="openItem($event, item, close)"
          >
            <span
              class="mt-1.5 size-2 shrink-0 rounded-full"
              :class="item.read ? 'bg-transparent' : 'bg-surface-blue-5'"
              aria-hidden="true"
            />
            <span class="min-w-0 flex-1">
              <span class="line-clamp-2 block" :class="item.read ? 'text-ink-gray-6' : 'text-ink-gray-9'">{{ item.subject || item.type }}</span>
              <span class="mt-0.5 block text-p-xs text-ink-gray-5">
                {{ [item.from_user, when.format(new Date(item.creation.replace(' ', 'T')))].filter(Boolean).join(' · ') }}
              </span>
            </span>
          </a>
        </div>
      </div>
    </template>
  </Popover>
</template>
