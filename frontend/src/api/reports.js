import { apiPost } from './client.js'

// 신고는 접수만 한다. 신고 내용을 읽어 오는 요청은 없다. (운영자는 데이터베이스 화면에서 확인)
// targetType: 'study' | 'todo' | 'error' | 'comment'
export const createReport = (targetType, targetId, reason) =>
  apiPost('/reports', { target_type: targetType, target_id: targetId, reason })
