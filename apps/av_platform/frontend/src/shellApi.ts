// Global header of the shell (UI-05): search and notifications from av_platform.shell. The server
// checks permissions and builds every link; the client only shows the answers.
import { router } from './router'

export interface SearchResult {
  doctype: 'Project' | 'Task' | 'Quotation' | 'Customer'
  name: string
  title: string
  subtitle: string | null
  href: string
}

export interface NotificationItem {
  name: string
  subject: string
  type: string | null
  from_user: string | null
  read: boolean
  creation: string
  href: string | null
}

export interface Notifications {
  items: NotificationItem[]
  unread: number
}

const METHOD = '/api/v2/method/'
const NOTIFICATION_LOG = 'frappe.desk.doctype.notification_log.notification_log'

async function request<T>(method: string, params?: Record<string, string>, post = false): Promise<T> {
  const query = !post && params ? `?${new URLSearchParams(params)}` : ''
  const response = await fetch(METHOD + method + query, {
    method: post ? 'POST' : 'GET',
    headers: {
      Accept: 'application/json',
      ...(post ? { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token ?? '' } : {}),
    },
    body: post ? JSON.stringify(params ?? {}) : undefined,
  })
  if (!response.ok) throw new Error(`${method}: HTTP ${response.status}`)
  return ((await response.json()) as { data: T }).data
}

export const searchRecords = (text: string) => request<SearchResult[]>('av_platform.shell.search', { text })
export const loadNotifications = () => request<Notifications>('av_platform.shell.get_notifications')
export const markRead = (docname: string) => request<null>(`${NOTIFICATION_LOG}.mark_as_read`, { docname }, true)
export const markAllRead = () => request<null>(`${NOTIFICATION_LOG}.mark_all_as_read`, {}, true)

/**
 * Follows a link from the header: a shell address opens without a reload, Desk opens as a page.
 * A modified click keeps the browser default (new tab or window).
 */
export function follow(event: MouseEvent | KeyboardEvent, href: string) {
  if (event instanceof MouseEvent && (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0)) return
  event.preventDefault()
  if (href.startsWith('/av/')) router.push(href.slice(3))
  else window.location.href = href
}
