import { apiGet, apiPatch, apiPost } from './client.js'

export const signup = (email, password, nickname) => apiPost('/auth/signup', { email, password, nickname })
export const login = (email, password) => apiPost('/auth/login', { email, password })
export const logout = () => apiPost('/auth/logout')
export const fetchMe = () => apiGet('/auth/me')
export const changeNickname = (nickname) => apiPatch('/auth/me/nickname', { nickname })
