# Next Session

> Volatile hot context. Overwrite this file on each meaningful handoff only when navigation/state changes. Task prompts and their evidence stay in the owning Phase; do not copy an executable task prompt here.

Outcome: IN PROGRESS

## Current phase
Phase 00 — Technical Proof (TP Gate)

## Completed this session
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
- Задания для TP-02–TP-04 в `00-technical-proof.prompts.md` ещё не написаны.

## Next action
TP-02 — целостность и полномочия Sales → PM: браузерный сценарий под Sales и PM и проверка всех read-путей (API, список, поиск, отчёт, экспорт, вложения). Сначала записать задание tp-02-r1 в `.progressive/phases/00-technical-proof.prompts.md` по PROTOTYPE-BRIEF §8.

## Active task prompt
NONE
