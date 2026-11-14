# Architecture — AV Integration Business Platform

Решение и обоснование — [ADR-001](../decisions/ADR-001-frappe-typescript-hybrid.md), оболочка — [ADR-004](../decisions/ADR-004-desk-as-product-shell.md); полный стек и правила — [MVP-SPEC §2.3](../../MVP-SPEC.md#23-техническая-основа-и-стек). Здесь — текущее устройство и целевые границы.

## Recommended stack
- Runtime/framework: Frappe v16 + ERPNext v16 (Python) — сервер, DocType, права, бизнес-правила. Своё приложение `apps/av_platform` расширяет ERPNext без правки core: `doc_events`, `extend_doctype_class`, `override_whitelisted_methods`, custom fields/fixtures, свои DocType и патчи.
- Frontend: Frappe Desk — единственная оболочка продукта (своя панель модулей, меню и страницы приложения). Экраны, которых нет в Desk, — TypeScript + Vue 3 + frappe-ui внутри страниц Desk, стили изолированы контейнером `.av-desk`. React-острова (Excalidraw, React Flow) для схем. Поле — после проверки Desk на телефоне.
- Data/storage: MariaDB (документированная основа ERPNext), файлы Frappe (public/private), Redis.
- Collaboration: отдельный Node-сервис Hocuspocus (Yjs), доступ по сессии Frappe.
- AI ([ADR-005](../decisions/ADR-005-ai-gateway-local-and-external-models.md)): встроенный MCP Frappe (с v16.55) для внешних агентов; ассистент продукта в `av_platform` (Python, фоновые задания, realtime); модели через один шлюз с OpenAI-совместимым API — локальные на офисном GPU-сервере (Ollama → vLLM) и внешние провайдеры.
- Deployment: Docker Compose (официальная схема frappe_docker) — пока только локальный прототип.

## Why this fits
Готовые права, журнал, отчёты, Desk, закупка/склад/проекты ERPNext и встроенный MCP сокращают объём разработки; TypeScript-фронтенды — штатный путь Frappe (Frappe CRM, Raven), поэтому чужой JS-код и React-компоненты встраиваются без переписывания. AV-логика по опыту референсов (D-Tools SI, Jetbuilt, CxAlloy, Fieldwire и др., [research/02](../../research/02-reference-products.md)) добавляется своим приложением поверх ERPNext.

## System shape
```text
[Frappe Desk: оболочка, списки, формы  ⊃  Vue+frappe-ui страницы ролей]   [MCP-клиент ИИ]
                          |                                                     /
         +---------- Frappe REST/RPC + permissions + MCP (/api/v2/mcp) ----+
                                   |
        av_platform (AV-домен: handover, release, deployment, tests, EAC)
                                   |
        ERPNext (Customer, Item, Quotation, Project, PO, Receipt, Stock, Serial No)
                                   |
                     MariaDB · files · Redis         Hocuspocus (Node, Yjs) — сбоку

av_platform (ассистент) → шлюз моделей (OpenAI-совместимый API, ключи, журнал)
                            ├─ локально: vLLM / Ollama на офисном GPU-сервере
                            └─ внешние провайдеры — только разрешённые классификацией данные
```

## Current state (observed in repository)
- Реализован только срез Sales → PM: DocType `AV Handover`, `commercial.py`, `permissions.py`; зависит от ERPNext (`required_apps = ["erpnext"]`), использует Quotation и Project.
- Образ `frappe/erpnext:v16.53.0` по digest, MariaDB 11.8.3, Redis 7.4.6; фактическая версия Frappe в образе — 16.55.1. Runtime запущен 12.11.2026 (TP-01: up, seed, 11 Frappe-тестов — PASS; restore, браузер, конкурентность — NOT RUN).
- Экраны ролей (доска предложений, доска работ, «Мои задачи») — Vue 3 + frappe-ui в страницах Desk `av-quotations`, `av-work-board`, `av-my-tasks`; меню `AV Sales` и `AV Projects`, иконки в панели модулей (`av_platform/dock`, `av_platform/av_platform/sidebar`). Бандл собирается Vite в `public/frontend`, путь передаётся при входе (`av_platform/desk.py`).
- Hocuspocus, MCP, шлюза моделей и ассистента пока нет (ADR-005 — Specified).

## Sources of truth
- Владельцы каждого факта — [MVP-SPEC §5](../../MVP-SPEC.md#5-логическая-модель-и-источники). Коротко: заказ/получение/склад — ERPNext; AV-размещение, конфигурации, проверки, передачи — av_platform; бухгалтерский факт — учёт компании или ERPNext по решению Q2/Q3.
- Второй складской, проектный или финансовый журнал не создаётся.

## Security/trust boundaries
- Все решения о статусах, правах и деньгах — только на сервере Frappe; фронтенды и Node-сервисы их не принимают.
- Права проверяются во всех каналах: формы, API, отчёты, поиск, экспорт, вложения, MCP. Коммерческие вложения недоступны полевым ролям.
- ИИ: чат в продукте — в сессии человека с разрешённым ИИ списком инструментов; внешние MCP-клиенты и фоновые задачи — под отдельным пользователем ИИ. Действия — только через «Предложение ИИ» с подтверждением. Закрытые данные — только локальной модели. Содержимое документов — данные, не инструкции. Ключи провайдеров — только в шлюзе.
- Секреты среды — `.runtime/` вне Git.

## Operational assumptions
- Разработка на Windows через Docker/WSL2; Frappe официально только Linux/macOS.
- Одна компания в эксплуатации; модель не исключает нескольких (ARC-01). Способ эксплуатационной изоляции (сайт на компанию или общая база) выбирается до второй компании.

## Architecture-change triggers
- TP Gate или P2–P8 показывают, что AV-сценарии не укладываются в ERPNext без правки core или с двойным учётом.
- Лицензионный разбор (Q10) запрещает выбранную модель распространения с ERPNext (GPL-3.0).
- Полевая проверка (Q5) требует полного offline.
- Нужна вторая компания в эксплуатации.
