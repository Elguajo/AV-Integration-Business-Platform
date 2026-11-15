// Data the server renders into the /av page before the app starts (av_platform.shell.boot).
export type ViewKey = 'home' | 'my-tasks' | 'projects' | 'board' | 'sales'

export interface ShellBoot {
  user: string
  full_name: string
  image: string | null
  /** Screens this user may open, in menu order. */
  views: ViewKey[]
  /** Start page after login: "av/<route>" for a shell screen, anything else is outside the shell. */
  landing: string | null
  /** Whether the user may open Desk (system users only). */
  desk: boolean
}

declare global {
  interface Window {
    av_boot?: ShellBoot
  }
}

export const boot: ShellBoot = window.av_boot ?? {
  user: 'Guest',
  full_name: '',
  image: null,
  views: [],
  landing: null,
  desk: false,
}

/** Route of the user's start screen inside the shell. */
export function landingPath(): string {
  const route = boot.landing?.startsWith('av/') ? boot.landing.slice(3) : null
  if (route && boot.views.includes(route as ViewKey)) return `/${route}`
  return boot.views.length ? `/${boot.views[0]}` : '/home'
}
