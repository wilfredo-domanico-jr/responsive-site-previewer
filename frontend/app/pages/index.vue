<script setup lang="ts">
import type { DeviceKey, ViewMode } from '~/types/preview'

const { job, error, isRunning, start, client } = usePreviewJob()

const view = ref<ViewMode>('grid')
const activeDevice = ref<DeviceKey>('desktop')
const previewSection = ref<HTMLElement | null>(null)

const hasPreviews = computed(() => job.value !== null && Object.keys(job.value.previews).length > 0)

async function onSubmit(url: string) {
  view.value = 'grid'
  await start(url)
  if (job.value && import.meta.client) {
    await nextTick()
    previewSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function openLarge(device: DeviceKey) {
  activeDevice.value = device
  view.value = 'large'
}

// When the capture finishes, keep the large view on a device that has an image.
watch(hasPreviews, (ready) => {
  if (ready && job.value && !job.value.previews[activeDevice.value]) {
    const first = (Object.keys(job.value.previews) as DeviceKey[])[0]
    if (first) activeDevice.value = first
  }
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 pb-16 pt-6 sm:px-6 sm:pt-8 lg:gap-14">
    <header class="flex items-center justify-between">
      <NuxtLink to="/" class="flex items-center gap-2.5 text-ink">
        <AppLogo class="h-7 w-auto text-accent" />
        <span class="text-base font-semibold tracking-tight">Responsive Site Previewer</span>
      </NuxtLink>
      <span class="hidden text-sm text-ink-3 sm:inline">Four viewports, one pass</span>
    </header>

    <!-- hero: the input is the product -->
    <section class="mx-auto w-full max-w-3xl">
      <h1 class="text-balance text-3xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
        See any website at desktop, laptop, tablet and mobile sizes.
      </h1>
      <p class="mt-4 max-w-xl text-base text-ink-2 sm:text-lg">
        Paste a public address and get four full-page screenshots in one pass, ready to compare or download.
      </p>
      <div class="mt-8">
        <UrlForm :busy="isRunning" @submit="onSubmit" />
      </div>
      <div v-if="error" class="mt-4">
        <ErrorBanner :message="error" @dismiss="error = null" />
      </div>
    </section>

    <!-- preview dashboard -->
    <section
      ref="previewSection"
      class="scroll-mt-6 rounded-3xl bg-surface p-4 ring-1 ring-line-2 sm:p-6 lg:p-8"
      aria-labelledby="preview-heading"
    >
      <span id="preview-heading" class="sr-only">Preview</span>
      <PreviewToolbar v-model:view="view" :job="job" />

      <div class="mt-6 lg:mt-8">
        <PreviewGrid
          v-if="view === 'grid'"
          :job="job"
          :image-url="client.imageUrl"
          :download-url="client.downloadUrl"
          @open="openLarge"
        />
        <PreviewLarge
          v-else
          v-model:active="activeDevice"
          :job="job"
          :image-url="client.imageUrl"
          :download-url="client.downloadUrl"
        />
      </div>
    </section>

    <footer class="text-center text-xs text-ink-3">
      Screenshots are captured with headless Chromium at exactly 1920×1080, 1440×900, 768×1024 and 390×844.
    </footer>
  </div>
</template>
