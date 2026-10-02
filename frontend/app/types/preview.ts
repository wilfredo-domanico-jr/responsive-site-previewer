export type DeviceKey = 'desktop' | 'laptop' | 'tablet' | 'mobile'

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed'

export interface PreviewImage {
  width: number
  height: number
  image: string
}

export interface JobResponse {
  job_id: string
  url: string
  status: JobStatus
  step: string
  error: string | null
  previews: Partial<Record<DeviceKey, PreviewImage>>
  created_at: string
}

export interface DeviceMeta {
  key: DeviceKey
  label: string
  width: number
  height: number
}

export const DEVICES: readonly DeviceMeta[] = [
  { key: 'desktop', label: 'Desktop', width: 1920, height: 1080 },
  { key: 'laptop', label: 'Laptop', width: 1440, height: 900 },
  { key: 'tablet', label: 'Tablet', width: 768, height: 1024 },
  { key: 'mobile', label: 'Mobile', width: 390, height: 844 },
] as const

export type ViewMode = 'grid' | 'large'
