import { apiGet } from './client.js'

export function listPublic(kind = 'all', q = '') {
  const keyword = q.trim()
  return apiGet(`/public?kind=${kind}${keyword ? `&q=${encodeURIComponent(keyword)}` : ''}`)
}
