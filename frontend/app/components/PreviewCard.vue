<script setup lang="ts">
import type { DeviceMeta, JobStatus, PreviewImage } from '~/types/preview'

const props = defineProps<{
  device: DeviceMeta
  preview: PreviewImage | null
  jobStatus: JobStatus | null
  imageSrc: string | null
  downloadHref: string | null
  /** Step string from the backend, used to show which device is being captured. */
  step: string | null
}>()

const emit = defineEmits<{ open: [] }>()

const isCapturing = computed(
  () => props.preview === null && props.jobStatus === 'running' && props.step === `Capturing ${props.device.label.toLowerCase()}...`,
)
const isWaiting = computed(
  () => props.preview === null && (props.jobStatus === 'queued' || props.jobStatus === 'running') && !isCapturing.value,
)
const isIdle = computed(() => props.preview === null && (props.jobStatus === null || props.jobStatus === 'failed'))

const stateLabel = computed(() => {
  if (props.preview) return 'Captured'
  if (isCapturing.value) return 'Capturing'
  return 'Waiting'
})
</script>

<template>
  <article class="flex min-w-0 flex-col gap-3">
    <header class="flex items-baseline justify-between gap-2">
      <h3 class="flex items-center gap-1.5 text-sm font-semibold text-ink">
        <DeviceIcon :device="device.key" class="text-ink-2" />
        {{ device.label }}
      </h3>
      <span class="tnum text-xs text-ink-3">{{ device.width }}×{{ device.height }}</span>
    </header>

    <!-- device frame; aspect ratio = viewport ratio so the lineup reads as real devices -->
    <component
      :is="imageSrc ? 'button' : 'div'"
      :type="imageSrc ? 'button' : undefined"
      class="group relative block w-full overflow-hidden rounded-[14px] bg-frame p-[5px] text-left shadow-card transition-transform"
      :class="imageSrc ? 'cursor-zoom-in hover:-translate-y-0.5 focus-visible:-translate-y-0.5' : ''"
      :aria-label="imageSrc ? `Open large ${device.label.toLowerCase()} preview` : undefined"
      @click="imageSrc && emit('open')"
    >
      <div
        class="relative w-full overflow-hidden rounded-[10px] bg-surface-2"
        :style="{ aspectRatio: `${device.width} / ${device.height}` }"
      >
        <img
          v-if="imageSrc"
          :src="imageSrc"
          :alt="`${device.label} screenshot at ${device.width} by ${device.height} pixels`"
          class="fade-in absolute inset-0 h-full w-full object-cover object-top"
          loading="lazy"
          decoding="async"
        >
        <div v-else-if="isCapturing || isWaiting" class="skeleton absolute inset-0" aria-hidden="true" />
        <div v-else-if="isIdle" class="absolute inset-0 grid place-items-center text-ink-3" aria-hidden="true">
          <DeviceIcon :device="device.key" class="text-3xl opacity-50" />
        </div>
      </div>

      <span
        v-if="!isIdle"
        class="pointer-events-none absolute left-3 top-3 rounded-md px-2 py-0.5 text-xs font-medium backdrop-blur"
        :class="[
          preview ? 'bg-surface/85 text-ink' : 'bg-frame/70 text-white/90',
          preview && !isCapturing ? 'opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100' : '',
        ]"
      >
        <span v-if="isCapturing" class="pulse mr-1 inline-block size-1.5 rounded-full bg-accent align-middle" aria-hidden="true" />
        {{ stateLabel }}
      </span>
    </component>

    <footer class="flex items-center justify-between gap-2">
      <span class="whitespace-nowrap text-xs text-ink-3" aria-live="polite">
        <template v-if="preview">Full page</template>
        <template v-else-if="isCapturing">Capturing…</template>
        <template v-else-if="isWaiting">Waiting</template>
        <template v-else>&nbsp;</template>
      </span>
      <a
        v-if="downloadHref"
        :href="downloadHref"
        download
        class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-accent ring-1 ring-line hover:bg-accent-soft"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="size-4" aria-hidden="true">
          <path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 19h14" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        Download
      </a>
    </footer>
  </article>
</template>
