import { apiDelete, apiGet, apiPost, apiPut } from './client.js'

// parent: 'studies'(공부 기록) 또는 'errors'(오류 기록). 할 일에는 댓글이 없다.
export const listComments = (parent, id) => apiGet(`/${parent}/${id}/comments`)
export const createComment = (parent, id, content) => apiPost(`/${parent}/${id}/comments`, { content })
export const updateComment = (commentId, content) => apiPut(`/comments/${commentId}`, { content })
export const deleteComment = (commentId) => apiDelete(`/comments/${commentId}`)
