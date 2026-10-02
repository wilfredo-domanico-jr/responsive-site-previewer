<script setup lang="ts">
import type { JobResponse, ViewMode } from '~/types/preview'

const props = defineProps<{
  job: JobResponse | null
  view: ViewMode
}>()

const emit = defineEmits<{
  'update:view': [view: ViewMode]
}>()

const statusText = computed(() => {
  const job = props.job
  if (!job) return 'Previews appear here once you generate one.'
  if (job.status === 'completed') return 'Four sizes captured.'
  if (job.status === 'failed') return 'Capture stopped.'
  return job.step
})

const isBusy = computed(() => props.job !== null && (props.job.status === 'queued' || props.job.status === 'running'))

const hostLabel = computed(() => {
  if (!props.job) return null
  try {
    return new URL(props.job.url).host
  } catch {
    return props.job.url
  }
})
</script>

<template>
  <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
    <div class="min-w-0">
      <h2 class="text-xl font-semibold tracking-tight">Preview</h2>
      <p class="mt-1 flex items-center gap-2 text-sm text-ink-2" aria-live="polite">
        <span v-if="isBusy" class="pulse inline-block size-2 rounded-full bg-accent" aria-hidden="true" />
        <span class="truncate">
          <span v-if="hostLabel" class="font-medium text-ink">{{ hostLabel }}</span>
          <span v-if="hostLabel" aria-hidden="true"> &nbsp;</span>
          <span>{{ statusText }}</span>
        </span>
      </p>
    </div>

    <div
      class="inline-flex self-start rounded-xl bg-surface-2 p-1 ring-1 ring-line-2 sm:self-auto"
      role="group"
      aria-label="Preview layout"
    >
      <button
        v-for="mode in (['grid', 'large'] as ViewMode[])"
        :key="mode"
        type="button"
        class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
        :class="props.view === mode ? 'bg-surface text-ink shadow-card' : 'text-ink-2 hover:text-ink'"
        :aria-pressed="props.view === mode"
        @click="emit('update:view', mode)"
      >
        {{ mode === 'grid' ? 'Grid' : 'Large' }}
      </button>
    </div>
  </div>
</template>
