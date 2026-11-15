<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, ErrorMessage, Skeleton, useCall } from 'frappe-ui'
import OverlayScroll from '../components/OverlayScroll.vue'
import { API, WORKSPACE_LIMIT, type QuotationRow, type Stage, type Workspace } from '../api'
import { ru } from '../i18n/ru'
import QuotationCard from '../components/QuotationCard.vue'
import QuotationPanel from '../components/QuotationPanel.vue'

// The open quotation lives in the address: /av/sales/<quotation>.
const props = defineProps<{ quotation?: string }>()
const router = useRouter()

const workspace = useCall<Workspace>({ url: API.workspace })

const BASE_COLUMNS: Stage[] = ['draft', 'issued', 'handover_pending', 'returned', 'accepted']
const OPTIONAL_COLUMNS: Stage[] = ['handover_draft', 'handover_unknown', 'superseded']

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

// The finished column is collapsed by default; the choice is remembered like other shell flags.
const FINISHED: Stage = 'accepted'
const FINISHED_PAGE = 20
const FLAG_KEY = 'av.sales.acceptedOpen'

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

const finishedOpen = ref(readFlag(FLAG_KEY))
const finishedLimit = ref(FINISHED_PAGE)

function toggleFinished() {
  finishedOpen.value = !finishedOpen.value
  finishedLimit.value = FINISHED_PAGE
  writeFlag(FLAG_KEY, finishedOpen.value)
}

// get_workspace is capped and returns no total: at the cap every count is a lower bound.
const truncated = computed(() => (workspace.data?.quotations.length ?? 0) >= WORKSPACE_LIMIT)

function rowsOf(stage: Stage) {
  return grouped.value.get(stage) ?? []
}

function countOf(stage: Stage) {
  return `${rowsOf(stage).length}${truncated.value ? '+' : ''}`
}

function visibleRows(stage: Stage) {
  const rows = rowsOf(stage)
  if (stage !== FINISHED) return rows
  // An opened quotation (deep link) stays visible even beyond the cap.
  const selected = props.quotation ? rows.findIndex((row) => row.name === props.quotation) : -1
  return rows.slice(0, Math.max(finishedLimit.value, selected + 1))
}

function hiddenCount(stage: Stage) {
  return stage === FINISHED ? rowsOf(stage).length - visibleRows(stage).length : 0
}

function open(name: string) {
  router.push(`/sales/${encodeURIComponent(name)}`)
}

function close() {
  router.push('/sales')
}

function onChanged() {
  workspace.reload()
}
</script>

<template>
  <div class="flex h-full flex-col bg-surface-base text-ink-gray-8">
    <div class="flex items-center justify-between gap-2 px-5 pt-3">
      <span class="text-sm text-ink-gray-5">{{ ru.page.subtitle }}</span>
      <Button
        icon-left="lucide-refresh-cw"
        :label="ru.page.refresh"
        :loading="workspace.loading"
        @click="workspace.reload()"
      />
    </div>

    <p
      v-if="truncated"
      class="mx-5 mt-2 rounded-4 bg-surface-amber-2 px-3 py-1.5 text-p-sm text-ink-amber-7"
      role="status"
    >
      {{ ru.page.truncated.replace('{n}', String(WORKSPACE_LIMIT)) }}
    </p>

    <div class="flex min-h-0 flex-1">
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

        <OverlayScroll v-else orientation="horizontal" class="h-full" content-class="flex w-max gap-3 px-5 pb-5 pt-4">
          <template v-for="stage in columns" :key="stage">
            <section
              v-if="stage === FINISHED && !finishedOpen"
              class="flex w-36 shrink-0 flex-col self-start rounded-6 bg-surface-gray-1 p-3"
              :aria-label="ru.stage[stage]"
            >
              <h2 class="text-base-semibold text-ink-gray-8">{{ ru.stage[stage] }}</h2>
              <span class="mt-1 text-sm tabular-nums text-ink-gray-5">{{ countOf(stage) }}</span>
              <Button
                class="mt-3"
                size="sm"
                icon-left="lucide-chevron-right"
                :label="ru.column.show"
                :aria-label="`${ru.column.expand}: ${ru.stage[stage]}`"
                :aria-expanded="false"
                @click="toggleFinished"
              />
            </section>

            <section
              v-else
              class="flex w-60 shrink-0 flex-col 2xl:w-72 rounded-6 bg-surface-gray-1"
              :aria-label="ru.stage[stage]"
            >
              <header class="px-3 pb-2 pt-3">
                <div class="flex items-center justify-between gap-2">
                  <h2 class="truncate text-base-semibold text-ink-gray-8">{{ ru.stage[stage] }}</h2>
                  <div class="flex shrink-0 items-center gap-1">
                    <span class="text-sm tabular-nums text-ink-gray-5">{{ countOf(stage) }}</span>
                    <Button
                      v-if="stage === FINISHED"
                      variant="ghost"
                      size="sm"
                      :label="ru.column.hide"
                      :aria-label="`${ru.column.collapse}: ${ru.stage[stage]}`"
                      :aria-expanded="true"
                      @click="toggleFinished"
                    />
                  </div>
                </div>
                <p class="mt-1 text-p-xs text-ink-gray-5">{{ ru.stageHint[stage] }}</p>
              </header>
              <OverlayScroll class="min-h-0 flex-1" content-class="space-y-2 px-2 pb-3">
                <QuotationCard
                  v-for="row in visibleRows(stage)"
                  :key="row.name"
                  :row="row"
                  :selected="row.name === props.quotation"
                  @select="open(row.name)"
                />
                <div v-if="hiddenCount(stage) > 0" class="space-y-1 px-1 pt-1 text-center">
                  <p class="text-p-xs text-ink-gray-5">
                    {{
                      ru.column.shownOf
                        .replace('{shown}', String(visibleRows(stage).length))
                        .replace('{total}', countOf(stage))
                    }}
                  </p>
                  <Button class="w-full" size="sm" :label="ru.column.more" @click="finishedLimit += FINISHED_PAGE" />
                </div>
                <p
                  v-if="!rowsOf(stage).length"
                  class="px-3 py-6 text-center text-p-sm text-ink-gray-4"
                >
                  {{ ru.empty.column }}
                </p>
              </OverlayScroll>
            </section>
          </template>
        </OverlayScroll>
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
  </div>
</template>
