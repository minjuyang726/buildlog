import { apiDelete, apiGet, apiPut } from './client.js'

// parent: 'studies'(공부 기록) 또는 'errors'(오류 기록). 할 일에는 좋아요가 없다.
export const getLike = (parent, id) => apiGet(`/${parent}/${id}/like`)
export const addLike = (parent, id) => apiPut(`/${parent}/${id}/like`)
export const removeLike = (parent, id) => apiDelete(`/${parent}/${id}/like`)
