# Architecture — AV Integration Business Platform

Решение и обоснование — [ADR-001](../decisions/ADR-001-frappe-typescript-hybrid.md), оболочка — [ADR-006](../decisions/ADR-006-own-shell-desk-as-back-office.md) (заменил ADR-004); полный стек и правила — [MVP-SPEC §2.3](../../MVP-SPEC.md#23-техническая-основа-и-стек). Здесь — текущее устройство и целевые границы.

## Recommended stack
- Runtime/framework: Frappe v16 + ERPNext v16 (Python) — сервер, DocType, права, бизнес-правила. Своё приложение `apps/av_platform` расширяет ERPNext без правки core: `doc_events`, `extend_doctype_class`, `override_whitelisted_methods`, custom fields/fixtures, свои DocType и патчи.
- Frontend: экраны ролей — своё приложение на `/av` (TypeScript + Vue 3 + frappe-ui + vue-router) с одной боковой панелью и меню по ролям; стили изолированы контейнером `.av-desk`. Frappe Desk — back-office: ERPNext, справочники, формы документов, администрирование. React-острова (Excalidraw, React Flow) для схем. Поле — страница монтажника в том же приложении.
- Data/storage: MariaDB (документированная основа ERPNext), файлы Frappe (public/private), Redis.
- Collaboration: отдельный Node-сервис Hocuspocus (Yjs), доступ по сессии Frappe.
- AI ([ADR-005](../decisions/ADR-005-ai-gateway-local-and-external-models.md)): встроенный MCP Frappe (с v16.55) для внешних агентов; ассистент продукта в `av_platform` (Python, фоновые задания, realtime); модели через один шлюз с OpenAI-совместимым API — локальные на офисном GPU-сервере (Ollama → vLLM) и внешние провайдеры.
- Deployment: Docker Compose (официальная схема frappe_docker) — пока только локальный прототип.

## Why this fits
Готовые права, журнал, отчёты, Desk, закупка/склад/проекты ERPNext и встроенный MCP сокращают объём разработки; TypeScript-фронтенды — штатный путь Frappe (Frappe CRM, Raven), поэтому чужой JS-код и React-компоненты встраиваются без переписывания. AV-логика по опыту референсов (D-Tools SI, Jetbuilt, CxAlloy, Fieldwire и др., [research/02](../../research/02-reference-products.md)) добавляется своим приложением поверх ERPNext.

## System shape
```text
[/av: Vue+frappe-ui рабочие места ролей]  [Frappe Desk: back-office, ERPNext, формы]   [MCP-клиент ИИ]
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
- Серверный срез Sales → PM: DocType `AV Handover`, `commercial.py`, `permissions.py`, `versions.py`; зависит от ERPNext (`required_apps = ["erpnext"]`), использует Quotation и Project. По U10 передаётся только актуальная версия предложения; временная группировка версий по клиенту и компании — H до модели сделки. Также реализованы Kanban работ и «Мои задачи» (`pm_board.py`, `pm_api.py`), обзор руководителя/реестр проектов (`overview.py`), ограничения создания Project и управление сотрудниками (`user_admin.py`). Это частичная реализация V1, не все её контуры.
- Образ `frappe/erpnext:v16.53.0` по digest, MariaDB 11.8.3, Redis 7.4.6; записанная фактическая версия Frappe — 16.55.1. Последние сохранённые свидетельства: TP Gate PASS на синтетике 14.11.2026 (TP-01–TP-04, включая браузер, конкурентность и восстановление); PRJ-01 — C1–C7 PASS; ADM-01 — 125/125 Frappe-тестов; UI-04 — 124/124 и браузер под PM/375 px 15.11.2026. Владельцы результатов и ограничений — [prototype/README.md](../../prototype/README.md), соответствующие разделы; это история запусков, не проверка текущей доступности runtime.
- Экраны ролей (главная, все проекты и карточка проекта, доска работ, «Мои задачи», «Мои предложения») — одно приложение на `/av` (`frontend/src/App.vue`, `router.ts`); страница `av_platform/www/av.py` отдаёт его с данными входа, меню и стартовая страница по ролям — `av_platform/shell.py`. Vite собирает бандл в `public/frontend` и шаблон `www/av.html`. Страниц, меню и иконок AV в Desk нет (UI-04).
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
- Целевой первый пилот — одна компания; эксплуатация на реальных данных ещё не подтверждена. Модель не исключает нескольких компаний (ARC-01). Способ эксплуатационной изоляции (сайт на компанию или общая база) выбирается до второй компании.

## Architecture-change triggers
- TP Gate или P2–P8 показывают, что AV-сценарии не укладываются в ERPNext без правки core или с двойным учётом.
- Лицензионный разбор (Q10) запрещает выбранную модель распространения с ERPNext (GPL-3.0).
- Полевая проверка (Q5) требует полного offline.
- Нужна вторая компания в эксплуатации.
