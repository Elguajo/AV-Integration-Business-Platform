# Architecture — AV Integration Business Platform

Решение и обоснование — [ADR-001](../decisions/ADR-001-frappe-typescript-hybrid.md); полный стек и правила — [MVP-SPEC §2.3](../../MVP-SPEC.md#23-техническая-основа-и-стек). Здесь — текущее устройство и целевые границы.

## Recommended stack
- Runtime/framework: Frappe v16 + ERPNext v16 (Python) — сервер, DocType, права, бизнес-правила. Своё приложение `apps/av_platform` расширяет ERPNext без правки core: `doc_events`, `extend_doctype_class`, `override_whitelisted_methods`, custom fields/fixtures, свои DocType и патчи.
- Frontend: Frappe Desk для офиса; TypeScript + Vue 3 + frappe-ui (Vite-фронтенд в приложении, PWA) для ролей и поля; React-острова (Excalidraw, React Flow) для схем; связь через frappe-js-sdk / frappe-react-sdk.
- Data/storage: MariaDB (документированная основа ERPNext), файлы Frappe (public/private), Redis.
- Collaboration: отдельный Node-сервис Hocuspocus (Yjs), доступ по сессии Frappe.
- AI: встроенный MCP Frappe (с v16.55) под отдельным пользователем ИИ с ограниченной ролью.
- Deployment: Docker Compose (официальная схема frappe_docker) — пока только локальный прототип.

## Why this fits
Готовые права, журнал, отчёты, Desk, закупка/склад/проекты ERPNext и встроенный MCP сокращают объём разработки; TypeScript-фронтенды — штатный путь Frappe (Frappe CRM, Raven), поэтому чужой JS-код и React-компоненты встраиваются без переписывания. AV-логика по опыту референсов (D-Tools SI, Jetbuilt, CxAlloy, Fieldwire и др., [research/02](../../research/02-reference-products.md)) добавляется своим приложением поверх ERPNext.

## System shape
```text
[Desk: офис] [Vue+frappe-ui: роли, поле PWA] [React-острова: схемы] [MCP-клиент ИИ]
        \               |                        |                    /
         +---------- Frappe REST/RPC + permissions + MCP (/api/v2/mcp) ----+
                                   |
        av_platform (AV-домен: handover, release, deployment, tests, EAC)
                                   |
        ERPNext (Customer, Item, Quotation, Project, PO, Receipt, Stock, Serial No)
                                   |
                     MariaDB · files · Redis         Hocuspocus (Node, Yjs) — сбоку
```

## Current state (observed in repository)
- Реализован только срез Sales → PM: DocType `AV Handover`, `commercial.py`, `permissions.py`; зависит от ERPNext (`required_apps = ["erpnext"]`), использует Quotation и Project.
- Образ `frappe/erpnext:v16.53.0` по digest, MariaDB 11.8.3, Redis 7.4.6; фактическая версия Frappe в образе — 16.55.1. Runtime запущен 12.11.2026 (TP-01: up, seed, 11 Frappe-тестов — PASS; restore, браузер, конкурентность — NOT RUN).
- Фронтендов на TypeScript, Hocuspocus и MCP пока нет.

## Sources of truth
- Владельцы каждого факта — [MVP-SPEC §5](../../MVP-SPEC.md#5-логическая-модель-и-источники). Коротко: заказ/получение/склад — ERPNext; AV-размещение, конфигурации, проверки, передачи — av_platform; бухгалтерский факт — учёт компании или ERPNext по решению Q2/Q3.
- Второй складской, проектный или финансовый журнал не создаётся.

## Security/trust boundaries
- Все решения о статусах, правах и деньгах — только на сервере Frappe; фронтенды и Node-сервисы их не принимают.
- Права проверяются во всех каналах: формы, API, отчёты, поиск, экспорт, вложения, MCP. Коммерческие вложения недоступны полевым ролям.
- ИИ работает под отдельной учётной записью; содержимое документов — данные, не инструкции.
- Секреты среды — `.runtime/` вне Git.

## Operational assumptions
- Разработка на Windows через Docker/WSL2; Frappe официально только Linux/macOS.
- Одна компания в эксплуатации; модель не исключает нескольких (ARC-01). Способ эксплуатационной изоляции (сайт на компанию или общая база) выбирается до второй компании.

## Architecture-change triggers
- TP Gate или P2–P8 показывают, что AV-сценарии не укладываются в ERPNext без правки core или с двойным учётом.
- Лицензионный разбор (Q10) запрещает выбранную модель распространения с ERPNext (GPL-3.0).
- Полевая проверка (Q5) требует полного offline.
- Нужна вторая компания в эксплуатации.
