# Phase 00 — Task prompts

## Task prompts

### tp-01-r1
Task: TP-01 — воспроизводимый запуск и запись версий
Status: DONE
Freshness: CHECKED 12.11.2026
Source: PROTOTYPE-BRIEF §8, задача TP-01
Supersedes: NONE

#### Request
```text
Summary: закрыть TP Gate существующего среза Sales → PM; первый шаг — TP-01 (PROTOTYPE-BRIEF §8).
```

#### Prompt
```text
Проверить, доступен ли Docker engine (docker info). Если доступен: из корня в PowerShell 7
выполнить .\prototype\manage.ps1 check, up, seed; затем повторно up и убедиться, что данные
сохранились. Записать commit, digest образов и фактические версии (bench version --format json)
в prototype/README.md без секретов.
Не входит: смена закреплённых версий, удаление volumes, установка WSL, перезагрузка Windows —
это делает пользователь. При недоступном engine записать BLOCKED с точной причиной и действием.
Граница приёмки: строка «Среда и повторяемость» TP Gate (PROTOTYPE-BRIEF §4.1).
```

#### Freshness check
12.11.2026: Docker engine 29.9.2 доступен после перезагрузки Windows и запуска Docker Desktop.

#### Current checkpoint
Выполнено. Изменения в рабочем дереве не закоммичены.

#### Outcome / evidence
- 05.11.2026: HOST-02 unavailable (docker info: отсутствует pipe; WSL-пакет отсутствует).
- 12.11.2026: check PASS; up PASS после исправления `site.py`; seed PASS после исправлений `demo.py` и `permissions.py`; повторные up/seed сохранили данные (Quotation = 2, AV Handover = 1); `manage.ps1 test` 11/11 PASS после исправления теста и удаления `--skip-test-records`. Версии: Frappe 16.55.1, ERPNext 16.53.0, MariaDB 11.8.3, Redis 7.4.6. Свидетельства и побочный эффект (тестовые записи ERPNext в сайте) — prototype/README.md.
- Не входило и NOT RUN: restore-check, браузер, конкурентность двумя соединениями (TP-02–TP-04).
