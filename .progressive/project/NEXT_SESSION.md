# Next Session

> Volatile hot context. Overwrite this file on each meaningful handoff only when navigation/state changes. Task prompts and their evidence stay in the owning Phase; do not copy an executable task prompt here.

Outcome: IN PROGRESS

## Current phase
Phase 00 — Technical Proof (TP Gate)

## Completed this session
- TP-03 (14.11.2026, задание tp-03-r1): `manage.ps1 concurrency-check` — одновременные и чередующиеся «Принять», сбой после создания Project, повтор; C1–C5 PASS, 70/70 Frappe-тестов. Найден и исправлен 404 у проигравших одновременных запросов (prototype/README.md, раздел TP-03). Осталось в TP Gate: TP-02 браузер, TP-04 восстановление.
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
- Задания для TP-03–TP-04 в `00-technical-proof.prompts.md` ещё не написаны (tp-02-r1 записано, IN PROGRESS).

## Next action
- TP-02 — по заданию tp-02-r1 (IN PROGRESS): права Task/Project по участию, браузерный поток Sales → PM.
- BRD-1 «действия и сведения на карточке» — когда пользователь скажет начинать; перед стартом записать задание brd-1-r1. BRD и TP-02 меняют `pm_api.py` — не вести параллельно в одних файлах.

## Active task prompt
.progressive/phases/00-technical-proof.prompts.md#tp-02-r1
