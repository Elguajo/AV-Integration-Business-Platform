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
  userMenu: 'Меню пользователя',
  create: {
    button: 'Создать',
    hint: 'Откроется форма в Desk',
    // Task is «работа» on every screen (board: «Новая работа»).
    doctypes: { Quotation: 'Предложение', Customer: 'Клиент', Task: 'Работа' } as Record<string, string>,
  },
  search: {
    button: 'Поиск',
    title: 'Поиск по AV Platform',
    placeholder: 'Проекты, работы, предложения, клиенты и разделы',
    screens: 'Разделы',
    create: 'Создать',
    loading: 'Ищем…',
    short: 'Введите хотя бы 2 символа, чтобы искать проекты, работы, предложения и клиентов',
    none: (text: string) =>
      `По «${text}» ничего не найдено среди доступных вам проектов, работ, предложений и клиентов`,
    error: 'Поиск не ответил. Попробуйте ещё раз',
    hints: '↑↓ — выбрать, Enter — открыть, Esc — закрыть',
    doctypes: {
      Project: 'Проекты',
      Task: 'Работы',
      Quotation: 'Предложения',
      Customer: 'Клиенты',
    } as Record<string, string>,
  },
  notifications: {
    button: 'Уведомления',
    unread: (count: number) => `Уведомления, непрочитанных: ${count}`,
    title: 'Уведомления',
    markAll: 'Прочитать все',
    empty: 'Уведомлений нет',
    error: 'Не удалось загрузить уведомления',
    retry: 'Повторить',
  },
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
