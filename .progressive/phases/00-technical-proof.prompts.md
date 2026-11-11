# Phase 00 — Task prompts

## Task prompts

### tp-01-r1
Task: TP-01 — воспроизводимый запуск и запись версий
Status: BLOCKED
Freshness: UNCHECKED
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
Не выполнялась в этой сессии. Последнее известное состояние — отчёт 05.11.2026: Docker engine недоступен.

#### Current checkpoint
Ждёт пользователя: перезагрузить Windows, запустить Docker Desktop; при сообщении об отсутствии WSL — `wsl --install --no-distribution` в PowerShell администратора.

#### Outcome / evidence
- 05.11.2026: HOST-02 unavailable (docker info: отсутствует pipe; WSL-пакет отсутствует) — prototype/README.md.
