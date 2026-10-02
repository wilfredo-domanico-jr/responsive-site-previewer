<script setup lang="ts">
import { DEVICES, type DeviceKey, type JobResponse } from '~/types/preview'

const props = defineProps<{
  job: JobResponse | null
  imageUrl: (path: string) => string
  downloadUrl: (jobId: string, device: DeviceKey) => string
}>()

const emit = defineEmits<{ open: [device: DeviceKey] }>()

function previewFor(key: DeviceKey) {
  return props.job?.previews[key] ?? null
}

function imageSrc(key: DeviceKey) {
  const preview = previewFor(key)
  return preview ? props.imageUrl(preview.image) : null
}

function downloadHref(key: DeviceKey) {
  const job = props.job
  return job && job.status === 'completed' && previewFor(key) ? props.downloadUrl(job.job_id, key) : null
}
</script>

<template>
  <!--
    Column widths are proportional to viewport widths (softened so mobile stays legible),
    and the frames sit on a shared baseline, so the lineup itself shows the size relationship.
  -->
  <div class="preview-lineup grid items-end gap-5 sm:gap-6">
    <PreviewCard
      v-for="device in DEVICES"
      :key="device.key"
      :device="device"
      :preview="previewFor(device.key)"
      :job-status="job?.status ?? null"
      :step="job?.step ?? null"
      :image-src="imageSrc(device.key)"
      :download-href="downloadHref(device.key)"
      @open="emit('open', device.key)"
    />
  </div>
</template>

<style scoped>
.preview-lineup {
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .preview-lineup {
    grid-template-columns: 1.6fr 1fr;
  }
}

@media (min-width: 1024px) {
  .preview-lineup {
    grid-template-columns: 2.4fr 2fr 1.3fr 1fr;
  }
}
</style>
