<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge, Button, ErrorMessage, ScrollArea, Skeleton, useCall } from 'frappe-ui'
import { API, type QuotationDetail } from '../api'
import { ru } from '../i18n/ru'
import { date, money, quantity } from '../format'
import HandoverDialog from './HandoverDialog.vue'

const props = defineProps<{ name: string }>()
const emit = defineEmits<{ close: []; changed: []; open: [name: string] }>()

// The panel is keyed by quotation name, so params are fixed for its lifetime.
const detail = useCall<QuotationDetail, { name: string }>({
  url: API.quotation,
  params: { name: props.name },
})
const dialogOpen = ref(false)

const d = computed(() => detail.data)
const currency = computed(() => d.value?.quotation.currency)

const handoverTheme = computed(() => {
  const status = d.value?.handover?.review_status
  return status === 'Accepted' ? 'green' : status === 'Returned' ? 'amber' : 'blue'
})

function deskUrl(doctype: string, name: string) {
  return `/app/${doctype}/${encodeURIComponent(name)}`
}

async function onHandedOver() {
  dialogOpen.value = false
  await detail.reload()
  emit('changed')
}
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="flex min-h-12 items-center justify-between gap-2 border-b border-outline-gray-1 px-4">
      <span class="truncate text-sm tabular-nums text-ink-gray-5">{{ props.name }}</span>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon="lucide-external-link"
          :tooltip="ru.detail.openDesk"
          :aria-label="ru.detail.openDesk"
          :href="deskUrl('quotation', props.name)"
        />
        <Button variant="ghost" icon="lucide-x" aria-label="Закрыть" @click="emit('close')" />
      </div>
    </div>

    <div v-if="detail.loading && !d" class="space-y-3 p-4">
      <Skeleton class="h-6 w-56" />
      <Skeleton class="h-4 w-40" />
      <Skeleton class="h-32 w-full" />
    </div>

    <div v-else-if="detail.error" class="p-4">
      <ErrorMessage :message="detail.error" />
    </div>

    <ScrollArea v-else-if="d" class="min-h-0 flex-1" viewport-class="px-4 pb-10 pt-4">
      <div class="space-y-6">
      <section>
        <h2 class="text-2xl text-ink-gray-9">{{ d.quotation.customer_name || d.quotation.party_name }}</h2>
        <dl class="mt-3 grid grid-cols-[8rem_1fr] gap-y-1.5 text-sm">
          <dt class="text-ink-gray-5">{{ ru.detail.date }}</dt>
          <dd class="text-ink-gray-7">{{ date(d.quotation.transaction_date) }}</dd>
          <dt class="text-ink-gray-5">{{ ru.detail.validTill }}</dt>
          <dd class="text-ink-gray-7">{{ date(d.quotation.valid_till) }}</dd>
          <dt class="text-ink-gray-5">{{ ru.detail.status }}</dt>
          <dd class="text-ink-gray-7">{{ d.quotation.status }}</dd>
        </dl>
      </section>

      <section v-if="d.versions.length > 1">
        <h3 class="text-sm text-ink-gray-5">{{ ru.detail.versions }}</h3>
        <div class="mt-2 flex flex-wrap gap-1.5">
          <button
            v-for="v in d.versions"
            :key="v.name"
            type="button"
            class="rounded-4 border px-2 py-1 text-sm tabular-nums"
            :class="
              v.name === d.quotation.name
                ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                : 'border-outline-gray-1 text-ink-gray-6 hover:bg-surface-gray-2'
            "
            :aria-current="v.name === d.quotation.name"
            @click="v.name !== d.quotation.name && emit('open', v.name)"
          >
            {{ ru.detail.version }} {{ v.version }} · {{ money(v.grand_total, v.currency) }}
          </button>
        </div>
      </section>

      <section>
        <h3 class="text-lg-semibold text-ink-gray-8">{{ ru.detail.mainScope }}</h3>
        <table class="mt-2 w-full text-sm">
          <thead>
            <tr class="text-left text-ink-gray-5">
              <th class="py-1.5 font-normal">{{ ru.detail.item }}</th>
              <th class="py-1.5 text-right font-normal">{{ ru.detail.qty }}</th>
              <th class="py-1.5 text-right font-normal">{{ ru.detail.amount }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-gray-1">
            <tr v-for="line in d.main_items" :key="line.idx">
              <td class="py-2 pr-2">
                <div class="text-ink-gray-8">{{ line.item_name || line.item_code }}</div>
                <div class="mt-0.5 text-xs text-ink-gray-5">
                  {{ line.item_code }} · {{ money(line.rate, currency) }}
                </div>
              </td>
              <td class="py-2 text-right tabular-nums text-ink-gray-7">{{ quantity(line.qty, line.uom) }}</td>
              <td class="py-2 text-right tabular-nums text-ink-gray-8">{{ money(line.amount, currency) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="mt-2 flex items-center justify-between border-t border-outline-gray-2 pt-2">
          <span class="text-sm text-ink-gray-6">{{ ru.detail.mainTotal }}</span>
          <span class="text-lg-semibold tabular-nums text-ink-gray-9">{{ money(d.main_total, currency) }}</span>
        </div>
        <div class="mt-1 flex items-center justify-between text-sm text-ink-gray-5">
          <span>{{ ru.detail.grandTotal }}</span>
          <span class="tabular-nums">{{ money(d.quotation.grand_total, currency) }}</span>
        </div>
      </section>

      <section v-if="d.alternatives.length">
        <h3 class="text-sm text-ink-gray-5">{{ ru.detail.alternatives }}</h3>
        <ul class="mt-2 space-y-1.5">
          <li
            v-for="line in d.alternatives"
            :key="line.idx"
            class="flex items-center justify-between gap-2 rounded-4 bg-surface-gray-1 px-2 py-1.5 text-sm"
          >
            <span class="truncate text-ink-gray-6">{{ line.item_name || line.item_code }}</span>
            <span class="shrink-0 tabular-nums text-ink-gray-5">
              {{ quantity(line.qty, line.uom) }} · {{ money(line.amount, currency) }}
            </span>
          </li>
        </ul>
      </section>

      <section class="space-y-3">
        <h3 class="text-lg-semibold text-ink-gray-8">{{ ru.detail.handover }}</h3>

        <div v-if="d.handover" class="space-y-2 rounded-6 border border-outline-gray-1 p-3">
          <div class="flex items-center justify-between gap-2">
            <Badge
              :theme="handoverTheme"
              :label="ru.detail.handoverStatus[d.handover.review_status] ?? d.handover.review_status"
            />
            <a
              class="text-sm tabular-nums text-ink-blue-link"
              :href="deskUrl('av-handover', d.handover.name)"
              target="_blank"
              rel="noopener"
            >{{ d.handover.name }}</a>
          </div>
          <dl class="grid grid-cols-[8rem_1fr] gap-y-1.5 text-sm">
            <dt class="text-ink-gray-5">{{ ru.detail.pm }}</dt>
            <dd class="text-ink-gray-7">{{ d.handover.project_manager_name || d.handover.project_manager }}</dd>
            <template v-if="d.handover.reviewed_on">
              <dt class="text-ink-gray-5">{{ ru.detail.reviewedOn }}</dt>
              <dd class="text-ink-gray-7">{{ date(d.handover.reviewed_on) }}</dd>
            </template>
            <template v-if="d.handover.project">
              <dt class="text-ink-gray-5">{{ ru.detail.project }}</dt>
              <dd>
                <a
                  class="text-ink-blue-link"
                  :href="deskUrl('project', d.handover.project)"
                  target="_blank"
                  rel="noopener"
                >{{ d.handover.project }}</a>
              </dd>
            </template>
          </dl>
          <div
            v-if="d.handover.review_note"
            class="rounded-4 bg-surface-amber-2 px-2 py-1.5 text-p-sm text-ink-amber-7"
          >
            <span class="font-medium">{{ ru.detail.reviewNote }}:</span> {{ d.handover.review_note }}
          </div>
        </div>

        <p
          v-else-if="d.stage === 'handover_unknown'"
          class="rounded-4 bg-surface-gray-1 px-3 py-2 text-p-sm text-ink-gray-6"
        >
          {{ ru.detail.handoverHidden }}
        </p>

        <template v-else>
          <Button
            variant="solid"
            class="w-full"
            icon-left="lucide-arrow-right-left"
            :label="ru.detail.handoverAction"
            :disabled="!d.can_handover"
            @click="dialogOpen = true"
          />
          <ul v-if="!d.can_handover" class="space-y-1" :aria-label="ru.detail.cannotHandover">
            <li
              v-for="code in d.blockers"
              :key="code"
              class="flex gap-1.5 text-p-sm text-ink-gray-6"
            >
              <span class="lucide-info mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
              {{ ru.blocker[code] ?? code }}
            </li>
          </ul>
          <p class="text-p-xs text-ink-gray-5">{{ ru.detail.notEvidence }}</p>
        </template>
      </section>
      </div>
    </ScrollArea>

    <HandoverDialog
      v-if="d && d.can_handover"
      v-model:open="dialogOpen"
      :detail="d"
      @done="onHandedOver"
    />
  </div>
</template>
