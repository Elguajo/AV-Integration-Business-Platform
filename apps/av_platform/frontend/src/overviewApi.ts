// Shapes returned by av_platform.overview: home page (DIR-01, UI-03), project register and
// project card (UI-03). The server decides every stage, status and reason; the client only renders them.
import type { DueBucket, DueState, Person } from './pmApi'

export type FunnelStage = 'draft' | 'issued' | 'handover' | 'returned' | 'accepted'
export type DealAlert = 'expired' | 'expiring'
export type ProjectStatus = 'problem' | 'risk' | 'unknown' | 'on_plan'
export type ReasonCode =
  | 'blocked'
  | 'overdue'
  | 'milestone_soon'
  | 'no_works'
  | 'no_dates'
  | 'all_done'
  | 'undated'
  | 'unassigned'

export const STATUSES: ProjectStatus[] = ['problem', 'risk', 'unknown', 'on_plan']

export interface Amount {
  currency: string
  amount: number
}

export interface Deal {
  name: string
  title: string | null
  customer: string | null
  group: FunnelStage
  stage: string
  grand_total: number | null
  currency: string | null
  valid_till: string | null
  owner: Person | null
  project: string | null
  alert: DealAlert | null
}

export interface Funnel {
  stages: { stage: FunnelStage; count: number; totals: Amount[] }[]
  open_totals: Amount[]
  attention: Deal[]
  revisions: number
  truncated: boolean
}

export interface TaskRef {
  name: string
  subject: string
  end: string | null
  due: DueState | null
  assignees: Person[]
}

export interface ProjectRow {
  name: string
  project_name: string | null
  customer: string | null
  expected_end: string | null
  pm: Person | null
  team: Person[]
  mine: boolean
  basis: { amount: number | null; currency: string | null; quotation: string } | null
  works: { done: number; total: number }
  next_milestone: TaskRef | null
  obstacle: (TaskRef & { kind: 'blocked' | 'overdue'; reason: string | null }) | null
  status: ProjectStatus
  reasons: { code: ReasonCode; count: number }[]
}

export interface ProjectList {
  rows: ProjectRow[]
  truncated: boolean
}

export interface MyTaskItem {
  name: string
  subject: string
  project: string | null
  project_name: string | null
  end: string | null
  bucket: DueBucket
  block_reason: string | null
}

export interface MyTasksSummary {
  counts: Record<DueBucket, number>
  items: MyTaskItem[]
  truncated: boolean
}

export interface Overview {
  today: string
  user: Person
  funnel: Funnel | null
  my_tasks: MyTasksSummary | null
  projects: ProjectList
  status_counts: Record<ProjectStatus, number>
  money_visible: boolean
}

export interface ProjectRegister {
  today: string
  projects: ProjectList
  status_counts: Record<ProjectStatus, number>
  money_visible: boolean
}

export interface Work {
  name: string
  subject: string
  status: string
  stage: string | null
  end: string | null
  due: DueState | null
  bucket: DueBucket | null
  is_milestone: boolean
  block_reason: string | null
  assignees: Person[]
}

export interface ProjectCardData {
  today: string
  project: ProjectRow & {
    project_status: string
    expected_start: string | null
    handover: { name: string; reviewed_on: string | null } | null
  }
  stages: { name: string; label: string; is_closed: boolean }[]
  works: Work[]
  works_truncated: boolean
  obstacles: (Work & { kind: 'blocked' | 'overdue' })[]
  milestones: Work[]
  my_works: Work[]
  files: { name: string; file_name: string | null; file_url: string; is_private: boolean; creation: string }[]
  money_visible: boolean
}

export const OVERVIEW_API = {
  overview: '/api/v2/method/av_platform.overview.get_overview',
  projects: '/api/v2/method/av_platform.overview.get_projects',
  project: '/api/v2/method/av_platform.overview.get_project',
}

export function deskUrl(doctype: string, name: string) {
  return `/desk/${doctype.toLowerCase().replace(/ /g, '-')}/${encodeURIComponent(name)}`
}

export function pageUrl(page: string, ...args: string[]) {
  return ['/desk', page, ...args.map(encodeURIComponent)].join('/')
}

/** Opens a Desk page inside the running Desk (no reload); a modified click keeps the browser default. */
export function openPage(event: MouseEvent | KeyboardEvent, page: string, ...args: string[]) {
  if (event instanceof MouseEvent && (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0)) {
    return
  }
  event.preventDefault()
  window.frappe.set_route(page, ...args)
}
