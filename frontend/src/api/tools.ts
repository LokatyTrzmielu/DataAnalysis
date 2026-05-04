import client from './client'
import type { MappingInspectResponse } from './runs'
import type { Dataset } from './datasets'

export const toolsApi = {
  inspectFile: (file: File, file_type: 'masterdata' | 'orders') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('file_type', file_type)
    return client.post<MappingInspectResponse>('/tools/data-preparation/inspect', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  mergeFiles: (files: File[], file_type: 'masterdata' | 'orders', mapping: Record<string, string>, name?: string) => {
    const fd = new FormData()
    for (const file of files) fd.append('files', file)
    fd.append('file_type', file_type)
    fd.append('mapping_json', JSON.stringify(mapping))
    if (name) fd.append('name', name)
    return client.post<Dataset>('/tools/data-preparation/merge', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
