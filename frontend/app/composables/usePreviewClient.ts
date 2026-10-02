import { createPreviewClient, type PreviewClient } from '~/utils/previewClient'

/** Preview API client bound to the configured backend base URL. */
export function usePreviewClient(): PreviewClient {
  const config = useRuntimeConfig()
  return createPreviewClient(config.public.apiBase, (input, init) => fetch(input, init))
}
