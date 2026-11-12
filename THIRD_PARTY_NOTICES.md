# Third-party notices

Происхождение внешнего кода и ресурсов по [ADR-003](.progressive/decisions/). Заимствованный код в репозиторий не копировался: перечисленные пакеты подключаются как зависимости и попадают только в собранные файлы.

## Фронтенд рабочих мест (`apps/av_platform/frontend`)

Собранный бандл лежит в `apps/av_platform/av_platform/public/frontend`. Версии закреплены в `apps/av_platform/frontend/package.json`; полный состав — в `package-lock.json`. Проверено 12.11.2026.

| Компонент | Версия | Лицензия | Источник | Как используется |
|---|---|---|---|---|
| frappe-ui | 1.2.0 | MIT, © 2022 Frappe Technologies Pvt. Ltd. | [frappe/frappe-ui](https://github.com/frappe/frappe-ui) | Компоненты, токены, Vite-плагин; входит в бандл |
| Inter (шрифт) | поставляется с frappe-ui 1.2.0 | SIL OFL 1.1 | [rsms/inter](https://github.com/rsms/inter) | Файлы `Inter*.woff2` в бандле |
| Vue | 3.5.45 | MIT | [vuejs/core](https://github.com/vuejs/core) | Входит в бандл |
| Vue Router | 4.6.4 | MIT | [vuejs/router](https://github.com/vuejs/router) | Входит в бандл |
| reka-ui, vue-sonner | зависимости frappe-ui | MIT | npm | Входят в бандл через frappe-ui |
| DOMPurify | зависимость frappe-ui | MPL-2.0 OR Apache-2.0 | [cure53/DOMPurify](https://github.com/cure53/DOMPurify) | Входит в бандл через frappe-ui; используется на условиях Apache-2.0 |

Инструменты сборки (Vite, Tailwind CSS 3, TypeScript, vue-tsc, PostCSS, Autoprefixer) в бандл не входят.

## Что не используется

- Frappe CRM и Helpdesk — AGPL-3.0. Код не копировался; устройство рабочего места Sales построено по документации frappe-ui и макетам проекта (`docs/visuals`).
- `frappe/frappe-ui-starter` — в репозитории нет лицензии, шаблон устарел для frappe-ui 1.x; конфигурация написана по официальной инструкции frappe-ui.
