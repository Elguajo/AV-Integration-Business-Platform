# Phase 00 — Technical Proof (TP Gate)

## Goal
Существующий срез Sales → PM воспроизводимо запускается на Frappe/ERPNext v16 и проходит все строки TP Gate с записанными свидетельствами.

## Context
- Критерии TP Gate — [PROTOTYPE-BRIEF §4.1](../../PROTOTYPE-BRIEF.md#41-первый-барьер-technical-proof-tp-gate); очередь TP-01–TP-04 — [§8](../../PROTOTYPE-BRIEF.md#8-ближайшая-очередь-проверки); результаты запусков записываются в [prototype/README.md](../../prototype/README.md).
- На 12.11.2026 runtime работает: check/up/seed и повторный запуск — PASS, 8 unit-проверок и 11 Frappe-тестов — PASS; браузер, конкурентность двумя соединениями и restore — NOT RUN. Подробности и исправления — prototype/README.md.
- Роль ERPNext решена: в ядре (U9). Фактическая версия Frappe в образе — 16.55.1 (порог встроенного MCP — 16.55).
- В сайте прототипа остались штатные тестовые записи ERPNext (`_Test Company` и др.) от диагностического запуска; тесты и учебные данные делят один сайт.

## Context hints
- `prototype/manage.ps1`, `prototype/compose.yml`, `prototype/Dockerfile`, `prototype/restore_check.py`
- `apps/av_platform/av_platform/commercial.py`, `permissions.py`, `av_platform/doctype/av_handover/`, `tests/test_commercial.py`

## In scope
- TP-01 воспроизводимый запуск: check/up/seed, повторный запуск, версии.
- TP-02 целостность и полномочия Sales → PM: unit, Frappe-тесты, браузерный поток, все read-пути.
- TP-03 конкурентность и откат: два независимых соединения, сбой после создания Project.
- TP-04 восстановление и итог TP Gate.

## Out of scope
- Новые рабочие места, фронтенды на TypeScript, модули Everything, MCP, P2–P8, реальные данные компании.
- Смена закреплённых версий или удаление volumes ради зелёного результата.
- Установка host-зависимостей и перезагрузка компьютера без явного согласия пользователя.

## Tasks
- [x] TP-01 — воспроизводимый запуск и запись версий (12.11.2026; изменения не закоммичены)
- [ ] TP-02 — целостность и полномочия Sales → PM
- [ ] TP-03 — конкурентность и откат
- [ ] TP-04 — восстановление и решение TP Gate

## Task prompts
Архив: `.progressive/phases/00-technical-proof.prompts.md`.

## Acceptance criteria
- [ ] Все строки TP Gate (среда, правила и интеграция, принятие и повтор, атомарность, версия и область, полномочия, браузер, восстановление) имеют PASS со свидетельством; неприменимые пути описаны с причиной.
- [ ] Записаны commit, digest и фактические версии Frappe, ERPNext, MariaDB, Redis.
- [ ] Ограничение «произвольное подмножество Q2 не поддерживается» зафиксировано.

## Negative / security cases
- Sales не принимает пакет; неназначенный PM не читает и не принимает его через форму, API, список, поиск, отчёт, экспорт и вложения.
- Подделка служебного флага через JSON отклоняется; обычное сохранение не переписывает submit.
- Введённая ошибка после создания Project не оставляет несогласованной пары.

## Verification
- `$env:PYTHONPATH = Join-Path (Get-Location) 'apps\av_platform'; python -m unittest discover -s tests -v`
- `.\prototype\manage.ps1 check`, `up`, `seed`, `test`, `restore-check` (PowerShell 7)
- Ручная браузерная проверка под Sales и PM на `http://localhost:8080`
- Итог каждой строки: PASS / FAIL / BLOCKED / NOT RUN в prototype/README.md

## Completion Record
