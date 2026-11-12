<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Button,
  DesktopShell,
  ErrorMessage,
  PageHeader,
  ScrollArea,
  Sidebar,
  SidebarHeader,
  SidebarItem,
  Skeleton,
  useCall,
} from 'frappe-ui'
import { API, type QuotationRow, type Stage, type Workspace } from '../api'
import { ru } from '../i18n/ru'
import QuotationCard from '../components/QuotationCard.vue'
import QuotationPanel from '../components/QuotationPanel.vue'

const props = defineProps<{ quotation?: string }>()
const router = useRouter()

const workspace = useCall<Workspace>({ url: API.workspace })

const BASE_COLUMNS: Stage[] = ['draft', 'issued', 'handover_pending', 'returned', 'accepted']
const OPTIONAL_COLUMNS: Stage[] = ['handover_draft', 'handover_unknown']

const grouped = computed(() => {
  const groups = new Map<Stage, QuotationRow[]>()
  for (const row of workspace.data?.quotations ?? []) {
    groups.set(row.stage, [...(groups.get(row.stage) ?? []), row])
  }
  return groups
})

const columns = computed(() => [
  ...BASE_COLUMNS,
  ...OPTIONAL_COLUMNS.filter((stage) => (grouped.value.get(stage) ?? []).length),
])

const forbidden = computed(() => (workspace.error as { type?: string } | null)?.type === 'PermissionError')
const isEmpty = computed(() => workspace.data && workspace.data.quotations.length === 0)

function open(name: string) {
  router.push({ name: 'Sales', params: { quotation: name } })
}

function close() {
  router.push({ name: 'Sales', params: {} })
}

function onChanged() {
  workspace.reload()
}
</script>

<template>
  <div class="h-screen w-full bg-surface-base text-ink-gray-8">
    <DesktopShell :scroll="false">
      <template #sidebar>
        <Sidebar width="14rem" class="border-r">
          <SidebarHeader :title="ru.app" :subtitle="workspace.data?.user.full_name ?? ru.role" />
          <div class="space-y-0.5 px-2 pt-0.5">
            <SidebarItem :label="ru.nav.quotations" icon="lucide-file-text" :route="{ name: 'Sales' }" active />
            <SidebarItem :label="ru.nav.desk" icon="lucide-external-link" href="/app" />
          </div>
        </Sidebar>
      </template>

      <PageHeader>
        <div class="flex w-full items-center justify-between gap-2">
          <div class="flex min-w-0 items-baseline gap-3">
            <h1 class="truncate text-lg-semibold text-ink-gray-9">{{ ru.page.title }}</h1>
            <span class="text-sm text-ink-gray-5">{{ ru.page.subtitle }}</span>
          </div>
          <Button
            icon-left="lucide-refresh-cw"
            :label="ru.page.refresh"
            :loading="workspace.loading"
            @click="workspace.reload()"
          />
        </div>
      </PageHeader>

      <div class="flex h-full min-h-0">
        <div class="min-w-0 flex-1" :class="{ 'hidden lg:block': props.quotation }">
          <div v-if="workspace.error" class="mx-auto max-w-xl px-5 pt-10">
            <p class="text-lg-semibold text-ink-gray-8">{{ ru.error.title }}</p>
            <p v-if="forbidden" class="mt-2 text-p-base text-ink-gray-6">{{ ru.error.forbidden }}</p>
            <ErrorMessage v-else class="mt-2" :message="workspace.error" />
          </div>

          <div v-else-if="workspace.loading && !workspace.data" class="flex gap-3 px-5 pt-5">
            <Skeleton v-for="i in 4" :key="i" class="h-60 w-72 shrink-0 rounded-6" />
          </div>

          <div
            v-else-if="isEmpty"
            class="flex flex-col items-center justify-center gap-3 py-24 text-center"
          >
            <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
              <span class="lucide-inbox size-6" aria-hidden="true" />
            </div>
            <p class="text-base text-ink-gray-7">{{ ru.empty.workspace }}</p>
            <p class="text-sm text-ink-gray-5">{{ ru.empty.workspaceHint }}</p>
          </div>

          <div v-else class="flex h-full gap-3 overflow-x-auto px-5 pb-5 pt-4">
            <section
              v-for="stage in columns"
              :key="stage"
              class="flex w-72 shrink-0 flex-col rounded-6 bg-surface-gray-1"
              :aria-label="ru.stage[stage]"
            >
              <header class="px-3 pb-2 pt-3">
                <div class="flex items-center justify-between">
                  <h2 class="text-base-semibold text-ink-gray-8">{{ ru.stage[stage] }}</h2>
                  <span class="text-sm tabular-nums text-ink-gray-5">
                    {{ (grouped.get(stage) ?? []).length }}
                  </span>
                </div>
                <p class="mt-1 text-p-xs text-ink-gray-5">{{ ru.stageHint[stage] }}</p>
              </header>
              <ScrollArea class="min-h-0 flex-1" viewport-class="space-y-2 px-2 pb-3">
                <QuotationCard
                  v-for="row in grouped.get(stage) ?? []"
                  :key="row.name"
                  :row="row"
                  :selected="row.name === props.quotation"
                  @select="open(row.name)"
                />
                <p
                  v-if="!(grouped.get(stage) ?? []).length"
                  class="px-3 py-6 text-center text-p-sm text-ink-gray-4"
                >
                  {{ ru.empty.column }}
                </p>
              </ScrollArea>
            </section>
          </div>
        </div>

        <aside
          v-if="props.quotation"
          class="w-full shrink-0 border-outline-gray-1 bg-surface-base lg:w-[26rem] lg:border-l"
        >
          <QuotationPanel
            :key="props.quotation"
            :name="props.quotation"
            @close="close"
            @changed="onChanged"
            @open="open"
          />
        </aside>
      </div>
    </DesktopShell>
  </div>
</template>
