import type { ReviewStatus } from '../data/stages'
import type { StatusKind } from '../components/StatusBadge.vue'

/** 将内容审核状态（ReviewStatus）映射为 StatusBadge 使用的语义状态。 */
export function statusToBadgeKind(status: ReviewStatus): StatusKind {
  return status === '已复核' ? 'verified' : 'pending'
}
