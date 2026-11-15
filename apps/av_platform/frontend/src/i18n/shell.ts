// Interface texts of the AV Platform shell (ADR-006).
import type { ViewKey } from '../boot'

export const ruShell = {
  app: 'AV Platform',
  menu: 'Разделы',
  openMenu: 'Открыть меню',
  closeMenu: 'Закрыть меню',
  collapse: 'Свернуть панель',
  expand: 'Развернуть панель',
  desk: 'Desk',
  deskHint: 'Справочники, документы ERPNext и администрирование',
  logout: 'Выйти',
  notFound: 'Такой страницы нет',
  toStart: 'На стартовую страницу',
  views: {
    home: 'Главная',
    'my-tasks': 'Мои задачи',
    projects: 'Все проекты',
    board: 'Доска работ',
    sales: 'Мои предложения',
  } satisfies Record<ViewKey, string>,
}

export const VIEW_ICONS: Record<ViewKey, string> = {
  home: 'lucide-house',
  'my-tasks': 'lucide-list-checks',
  projects: 'lucide-folder-kanban',
  board: 'lucide-square-kanban',
  sales: 'lucide-file-text',
}
