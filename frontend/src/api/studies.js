import { apiDelete, apiGet, apiPost, apiPut } from './client.js'

export function listStudies(q = '') {
  const keyword = q.trim()
  return apiGet(keyword ? `/studies?q=${encodeURIComponent(keyword)}` : '/studies')
}
export const getStudy = (id) => apiGet(`/studies/${id}`)
export const createStudy = (values) => apiPost('/studies', values)
export const updateStudy = (id, values) => apiPut(`/studies/${id}`, values)
export const deleteStudy = (id) => apiDelete(`/studies/${id}`)
