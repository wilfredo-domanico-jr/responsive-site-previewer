<script setup lang="ts">
import { DEVICES, type DeviceKey, type JobResponse } from '~/types/preview'

const props = defineProps<{
  job: JobResponse | null
  active: DeviceKey
  imageUrl: (path: string) => string
  downloadUrl: (jobId: string, device: DeviceKey) => string
}>()

const emit = defineEmits<{ 'update:active': [device: DeviceKey] }>()

const device = computed(() => DEVICES.find(d => d.key === props.active) ?? DEVICES[0]!)
const preview = computed(() => props.job?.previews[props.active] ?? null)
const imageSrc = computed(() => (preview.value ? props.imageUrl(preview.value.image) : null))
const downloadHref = computed(() =>
  props.job && props.job.status === 'completed' && preview.value ? props.downloadUrl(props.job.job_id, props.active) : null,
)
const isBusy = computed(() => props.job?.status === 'queued' || props.job?.status === 'running')
const isCapturingThis = computed(() => isBusy.value && props.job?.step === `Capturing ${device.value.label.toLowerCase()}...`)

function hasPreview(key: DeviceKey) {
  return Boolean(props.job?.previews[key])
}
</script>

<template>
  <section class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-1 rounded-xl bg-surface-2 p-1 ring-1 ring-line-2" role="tablist" aria-label="Device">
        <button
          v-for="d in DEVICES"
          :key="d.key"
          type="button"
          role="tab"
          :aria-selected="d.key === active"
          class="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
          :class="d.key === active ? 'bg-surface text-ink shadow-card' : 'text-ink-2 hover:text-ink'"
          @click="emit('update:active', d.key)"
        >
          <DeviceIcon :device="d.key" />
          <span>{{ d.label }}</span>
          <span class="tnum hidden text-xs text-ink-3 md:inline">{{ d.width }}×{{ d.height }}</span>
          <span
            v-if="hasPreview(d.key)"
            class="size-1.5 rounded-full bg-accent"
            aria-hidden="true"
          />
        </button>
      </div>

      <a
        v-if="downloadHref"
        :href="downloadHref"
        download
        class="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-accent-ink hover:brightness-110"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="size-4" aria-hidden="true">
          <path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 19h14" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        Download {{ device.label.toLowerCase() }} PNG
      </a>
    </div>

    <!-- The frame is as wide as the device viewport (scaled down to fit), so mobile really looks narrow. -->
    <div class="flex justify-center">
      <figure
        class="w-full rounded-[18px] bg-frame p-1.5 shadow-card"
        :style="{ maxWidth: `${device.width}px` }"
      >
        <div
          class="relative overflow-hidden rounded-[13px] bg-surface-2"
          :class="imageSrc ? 'max-h-[75vh] overflow-y-auto' : ''"
          :style="imageSrc ? undefined : { aspectRatio: `${device.width} / ${device.height}` }"
        >
          <img
            v-if="imageSrc"
            :src="imageSrc"
            :alt="`Full-page ${device.label.toLowerCase()} screenshot at ${device.width} by ${device.height} pixels`"
            class="fade-in block w-full"
            decoding="async"
          >
          <div v-else-if="isBusy" class="skeleton absolute inset-0" aria-hidden="true" />
          <div v-else class="absolute inset-0 grid place-items-center text-ink-3">
            <DeviceIcon :device="device.key" class="text-4xl opacity-50" />
          </div>
        </div>
        <figcaption class="flex items-center justify-between px-2 pt-1.5 pb-0.5 text-xs text-white/70">
          <span>{{ device.label }}</span>
          <span class="tnum">
            <template v-if="preview">{{ device.width }}×{{ device.height }} viewport, full page</template>
            <template v-else-if="isCapturingThis">Capturing…</template>
            <template v-else-if="isBusy">Waiting</template>
            <template v-else>{{ device.width }}×{{ device.height }}</template>
          </span>
        </figcaption>
      </figure>
    </div>
  </section>
</template>
