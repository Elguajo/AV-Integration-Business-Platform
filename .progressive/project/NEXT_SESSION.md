# Next Session

> Volatile hot context. Overwrite this file on each meaningful handoff only when navigation/state changes. Task prompts and their evidence stay in the owning Phase; do not copy an executable task prompt here.

Outcome: IN PROGRESS

## Current phase
Phase 00 — Technical Proof (TP Gate)

## Completed this session
- BRD-1 (14.11.2026, «Да, BRD-1», задание brd-1-r1): действия и сведения на карточке доски — завершить, следующий этап, переименование, «взять себе» и назначение участника проекта, номер и ссылка, комментарии, подзадачи «N/M» с раскрытием, срок «сегодня»/«скоро». 87/87 Frappe-тестов, браузер под PM и 375 px (prototype/README.md, раздел BRD-1).
- TP Gate пройден на синтетике (14.11.2026): TP-02 (Task/Project только участникам, access-check 0 утечек, браузер), TP-03 (другая сессия), TP-04 (restore PASS). Исправлено: PM не записывался участником принятого проекта. Итог — prototype/README.md, раздел TP-04.
- TP-03 (14.11.2026, задания tp-03-r1, tp-03-r2): `manage.ps1 concurrency-check` C1–C7 PASS, включая детерминированный «старый снимок» (C5) и цепочку решений в одной транзакции (C6). Первое исправление 404 в `d5833b5` теряло записи в цепочке вызовов; заменено проверкой видимости проекта, замена не закоммичена (prototype/README.md, раздел TP-03).
- ИИ (14.11.2026, U12, ADR-005 — Specified, ничего не запущено): модели через один шлюз — локальные на офисном GPU-сервере и внешние провайдеры; ассистент в `av_platform`; чат в сессии человека, MCP-клиенты под отдельным пользователем ИИ; действия только через «Предложение ИИ». Внедрение после TP Gate. AGENTS.md правило 6 уточнено по ADR-005 с согласия пользователя.
- UI-02 (14.11.2026, решение пользователя U11, ADR-004): Desk — основное окно продукта. Иконки «Продажи»/«Проекты», меню `AV Sales`/`AV Projects`, страницы Desk `av-quotations`, `av-work-board`, `av-my-tasks` с Vue-экранами; сайт `/av` убран (302). 54/54 Frappe-тестов, браузер под Sales и PM (prototype/README.md, раздел UI-02). AV — приложение по умолчанию; после входа Sales попадает в «Мои предложения», PM — в «Мои задачи» (59/59 тестов, вход через форму проверен).
- PM-01 (14.11.2026, решение пользователя): Kanban работ проекта `/av/board` — `AV Work Stage`, `pm_board.py`, `pm_api.py`, 16 Frappe-тестов, проверка в браузере под PM (prototype/README.md, раздел PM-01). Ждёт решения пользователя: ограничивать ли права Task/Project в Desk участием в проекте; следующий шаг PM-02–PM-04 — по поручению.
- PM-02 (14.11.2026, поручение пользователя): «Мои задачи» `/av/my-tasks` — `pm_api.get_my_tasks`, 10 Frappe-тестов, проверка в браузере под PM и на ширине 375 px (prototype/README.md, раздел PM-02). Следующий шаг PM-03 timeline или PM-04 whiteboard — по поручению.
- Разбор ClickUp и YouGile (14.11.2026, поручение пользователя): [research/07](../../research/07-work-management-reference.md) — предложения H для PM-01–PM-04 по документации, публичным API и просмотру аккаунтов пользователя только на чтение; сценарии с изменением данных NOT RUN. Whiteboard ClickUp построен на tldraw (лицензия source-available) — выбор Excalidraw (MIT) подтверждён.
- Доска YouGile в деталях (14.11.2026): research/07 §7 — справка, просмотр интерфейса на чтение (§7.1а), сравнение с PM-01; в прототипе проверено, что ERPNext не ведёт историю Task (`track_changes = 0`). По решению пользователя («сперва записал бы… потом поэтапно начал бы внедрять») доработка записана этапами BRD-1–BRD-7 в Phase 00; код не менялся.
- UI-01: рабочее место Sales на Vue 3 + frappe-ui (`/av/sales`), API `sales_api.py`, 17/17 Frappe-тестов, проверка в браузере (prototype/README.md).
- TP-01: Docker engine доступен; `manage.ps1 check/up/seed` и повторный запуск — PASS; `manage.ps1 test` — 11/11 PASS.
- Фактические версии записаны в prototype/README.md: Frappe 16.55.1, ERPNext 16.53.0, MariaDB 11.8.3, Redis 7.4.6.
- Исправлены `prototype/site.py`, `prototype/manage.ps1`, `av_platform/demo.py`, `av_platform/permissions.py`, `test_av_handover.py` (причины — prototype/README.md).
- На хост установлен PowerShell 7.7.0 (рядом с 5.1) с согласия пользователя.

## Verification evidence
- prototype/README.md, раздел «Состояние на 12 ноября 2026 (TP-01)».
- Ruff на хосте не установлен — статические проверки NOT RUN.

## Current working state
RUNNABLE / GREEN

Изменения в рабочем дереве не закоммичены. Контейнеры `av-prototype` запущены.

## Blockers / uncertainty
- Решение пользователя: можно ли передавать PM устаревшую версию предложения (сейчас сервер разрешает Q1 после передачи Q2).
- В сайте прототипа остались штатные тестовые записи ERPNext (`_Test Company` и др.). Очистка требует решения пользователя (сброс сайта = удаление volumes).
- MVP-SPEC §1 и PROTOTYPE-BRIEF (статус, строки P0/P1, §8) всё ещё описывают состояние 05.11.2026; MVP-SPEC меняется только с согласия пользователя.
- Роли закупки, склада и бухгалтерии не входят в правило «видит все проекты» (pm_board.ALL_PROJECTS_ROLES); добавить, когда появятся их рабочие места.
- Ruff на хосте не установлен — статические проверки NOT RUN.

## Next action
- TP Gate пройден (TP-01–TP-04). Следующий шаг по решению пользователя: полировка Desk (русский язык, скрытие лишних модулей ERPNext) или Phase 01 — разбор реального проекта (RP-01).
- BRD-2 «журнал переходов этапа» — по решению пользователя; перед стартом записать задание brd-2-r1. Этапы BRD меняют `pm_api.py` и `ProjectBoard.vue` — не вести параллельно в одних файлах; пересборку прототипа согласовывать с другими сессиями.

## Active task prompt
NONE
