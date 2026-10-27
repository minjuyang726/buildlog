import { apiDelete, apiGet, apiPost, apiPut } from './client.js'

export const listTodos = (filter = 'all') => apiGet(`/todos?filter=${filter}`)
export const getTodo = (id) => apiGet(`/todos/${id}`)
export const createTodo = (values) => apiPost('/todos', values)
export const updateTodo = (id, values) => apiPut(`/todos/${id}`, values)
export const setTodoDone = (id, isDone) => apiPut(`/todos/${id}/done`, { is_done: isDone })
export const deleteTodo = (id) => apiDelete(`/todos/${id}`)
