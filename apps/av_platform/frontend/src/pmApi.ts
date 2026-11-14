// Shapes returned by av_platform.pm_api (project work board, PM-01).
// The server owns every decision; the client only renders these values.

// One set of codes for every card action (move, rename, assign); texts live in i18n.
export type MoveRejection =
  | 'no_permission'
  | 'unknown_stage'
  | 'task_closed'
  | 'conflict'
  | 'blocked'
  | 'dependencies_open'
  | 'invalid_subject'
  | 'assign_forbidden'
  | 'assignee_not_member'

export type DueState = 'overdue' | 'today' | 'soon'

export interface Person {
  name: string
  full_name: string | null
}

export interface BoardStage {
  name: string
  label: string
  is_closed: boolean
}

export interface BoardTask {
  name: string
  subject: string
  project: string | null
  status: string
  priority: string | null
  stage: string | null
  block_reason: string | null
  room: string | null
  system: string | null
  start: string | null
  end: string | null
  is_overdue: boolean
  is_milestone: boolean
  assignees: Person[]
  modified: string
  due_state: DueState | null
  comments: number
  subtasks: { done: number; total: number } | null
}

export interface Board {
  user: Person
  stages: BoardStage[]
  projects: { name: string; project_name: string; members: Person[] }[]
  tasks: BoardTask[]
  truncated: boolean
  can_move: boolean
  can_assign_others: boolean
}

export interface Subtasks {
  task: string
  tasks: BoardTask[]
}

// "My tasks" (PM-02): the server assigns the due-date group using its own day.
export type MyTaskView = 'mine' | 'delegated'
export type DueBucket = 'overdue' | 'today' | 'week' | 'later' | 'no_date'

export interface MyTask extends BoardTask {
  bucket: DueBucket
}

export interface MyTasks {
  user: { name: string; full_name: string | null }
  view: MyTaskView
  today: string
  stages: BoardStage[]
  projects: { name: string; project_name: string }[]
  tasks: MyTask[]
  truncated: boolean
  can_move: boolean
}

export type MoveResult =
  | { ok: true; task: BoardTask }
  | { ok: false; code: MoveRejection; task: BoardTask | null }

export const PM_API = {
  board: '/api/v2/method/av_platform.pm_api.get_board',
  move: '/api/v2/method/av_platform.pm_api.move_task',
  rename: '/api/v2/method/av_platform.pm_api.rename_task',
  assign: '/api/v2/method/av_platform.pm_api.assign_task',
  unassign: '/api/v2/method/av_platform.pm_api.unassign_task',
  subtasks: '/api/v2/method/av_platform.pm_api.get_subtasks',
  myTasks: '/api/v2/method/av_platform.pm_api.get_my_tasks',
}

export function deskTaskUrl(name: string) {
  return `/desk/task/${encodeURIComponent(name)}`
}
