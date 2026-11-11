# ADR-001 — Основа: Frappe + ERPNext в ядре, интерфейсы на TypeScript/JS

Status: Accepted
Date: 2026-11-12

## Context
Нужна основа для рыночного продукта (U7), в которую можно быстро внедрять готовые решения с GitHub, сохраняя стабильность и безопасность. Сравнивались: собственное TypeScript + PostgreSQL, Payload, Django, Laravel + Filament, Odoo, NocoBase/Twenty/Directus и Frappe — [research/03 §9](../../research/03-platform-and-pilot.md#9-выбор-основы-12-ноября-2026). Модули HeyPuter/everything, которые пользователь хочет внедрять, написаны на чистом JS с сервером Puter.js (E5).

## Decision
- Frappe v16 (Python) — данные, права, бизнес-логика, журнал; единственный источник истины (U8, 12.11.2026: «Да, записать»).
- ERPNext — в ядре (U9, 12.11.2026: «Думаю стоит внедрить если можем улучшать его на основе опыта других референс продуктов»). Улучшения — только своим приложением `av_platform` без правки core (hooks `doc_events`, `extend_doctype_class`, `override_whitelisted_methods`, custom fields, свои DocType) по механизмам референсов из research/02.
- Интерфейсы ролей и поля — TypeScript + Vue 3 + frappe-ui, PWA; схемы — React-острова; совместное редактирование — Node + Hocuspocus; ИИ — встроенный MCP Frappe под ограниченным пользователем.

## Consequences
- Positive: готовые права, Desk, закупка, склад, проекты, Wiki, Gantt, MCP; TypeScript-фронтенды — штатный путь Frappe; чужой JS встраивается без переписывания.
- Cost/risk: два языка и отдельный Node-сервис; изоляция компаний в Frappe — сайт на базу; ERPNext под GPL-3.0 — распространение продукта у клиента может требовать открытия кода нашего приложения (проверить в Q10 до первой внешней компании); обновления ERPNext проверяются на копии данных.
- Revisit when: TP Gate или P2–P8 требуют правки core или двойного учёта; Q10 запрещает модель распространения; клиенты отказываются переходить на ERPNext для закупки и склада.
