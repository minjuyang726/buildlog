import { apiDelete, apiGet, apiPost, apiPut } from './client.js'

export function listErrors(filter = 'all', q = '') {
  const keyword = q.trim()
  const query = `filter=${filter}${keyword ? `&q=${encodeURIComponent(keyword)}` : ''}`
  return apiGet(`/errors?${query}`)
}
export const getError = (id) => apiGet(`/errors/${id}`)
export const createError = (values) => apiPost('/errors', values)
export const updateError = (id, values) => apiPut(`/errors/${id}`, values)
export const deleteError = (id) => apiDelete(`/errors/${id}`)
