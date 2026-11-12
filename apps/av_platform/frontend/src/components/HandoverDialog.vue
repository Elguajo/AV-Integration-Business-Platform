<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Alert, Button, Combobox, Dialog, ErrorMessage, FormControl, toast, useCall } from 'frappe-ui'
import { API, type QuotationDetail } from '../api'
import { ru } from '../i18n/ru'
import { money } from '../format'

const props = defineProps<{ detail: QuotationDetail }>()
const emit = defineEmits<{ done: [] }>()
const open = defineModel<boolean>('open', { required: true })

const form = reactive({
  project_manager: null as string | null,
  project_name: '',
  customer_approval_reference: '',
  start_authorization_reference: '',
})
const touched = ref(false)

watch(open, (value) => {
  if (!value) return
  touched.value = false
  form.project_manager = props.detail.pm_options.length === 1 ? props.detail.pm_options[0].name : null
  form.project_name = props.detail.quotation.customer_name || props.detail.quotation.party_name
  form.customer_approval_reference = ''
  form.start_authorization_reference = ''
  create.reset()
})

const pmOptions = computed(() =>
  props.detail.pm_options.map((u) => ({ label: u.full_name || u.name, value: u.name, description: u.name })),
)

const missing = computed(() => ({
  pm: !form.project_manager,
  name: !form.project_name.trim(),
  approval: !form.customer_approval_reference.trim(),
}))
const valid = computed(() => !Object.values(missing.value).some(Boolean))

const create = useCall<{ handover: string }, Record<string, unknown>>({
  url: API.createHandover,
  method: 'POST',
  immediate: false,
})

async function submit() {
  touched.value = true
  if (!valid.value) return
  await create.submit({
    quotation: props.detail.quotation.name,
    project_manager: form.project_manager,
    project_name: form.project_name.trim(),
    customer_approval_reference: form.customer_approval_reference.trim(),
    start_authorization_reference: form.start_authorization_reference.trim() || null,
  })
  if (create.error) return
  toast.success(ru.dialog.success, { description: create.data?.handover })
  emit('done')
}
</script>

<template>
  <Dialog v-model:open="open" :title="ru.dialog.title" size="xl">
    <form class="space-y-4" @submit.prevent="submit">
      <div class="rounded-6 bg-surface-gray-1 px-3 py-2 text-sm">
        <div class="flex justify-between gap-2">
          <span class="text-ink-gray-6">{{ detail.quotation.name }}</span>
          <span class="font-medium tabular-nums text-ink-gray-9">
            {{ money(detail.main_total, detail.quotation.currency) }}
          </span>
        </div>
        <div class="mt-0.5 text-xs text-ink-gray-5">{{ ru.detail.mainScope }}</div>
      </div>

      <Combobox
        v-model="form.project_manager"
        :options="pmOptions"
        :label="ru.dialog.pm"
        :placeholder="ru.dialog.pmPlaceholder"
        :empty-text="ru.dialog.noPm"
        :error="touched && missing.pm ? ru.dialog.required : undefined"
        required
      />
      <FormControl
        v-model="form.project_name"
        :label="ru.dialog.projectName"
        :error="touched && missing.name ? ru.dialog.required : undefined"
        required
      />
      <FormControl
        v-model="form.customer_approval_reference"
        type="textarea"
        :label="ru.dialog.approval"
        :description="ru.dialog.approvalHint"
        :error="touched && missing.approval ? ru.dialog.required : undefined"
        required
      />
      <FormControl
        v-model="form.start_authorization_reference"
        type="textarea"
        :label="ru.dialog.start"
        :description="ru.dialog.startHint"
      />

      <Alert theme="blue" :title="ru.dialog.noticeTitle" :description="ru.detail.notEvidence" />
      <ErrorMessage v-if="create.error" :message="create.error" />
    </form>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="ru.dialog.cancel" @click="open = false" />
        <Button variant="solid" :label="ru.dialog.submit" :loading="create.loading" @click="submit" />
      </div>
    </template>
  </Dialog>
</template>
