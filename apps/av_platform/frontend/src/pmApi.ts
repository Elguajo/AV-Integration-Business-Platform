// Shapes returned by av_platform.pm_api (project work board, PM-01).
// The server owns every decision; the client only renders these values.

export type MoveRejection =
  | 'no_permission'
  | 'unknown_stage'
  | 'task_closed'
  | 'conflict'
  | 'blocked'
  | 'dependencies_open'

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
  assignees: { name: string; full_name: string | null }[]
  modified: string
}

export interface Board {
  user: { name: string; full_name: string | null }
  stages: BoardStage[]
  projects: { name: string; project_name: string }[]
  tasks: BoardTask[]
  truncated: boolean
  can_move: boolean
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
  myTasks: '/api/v2/method/av_platform.pm_api.get_my_tasks',
}
