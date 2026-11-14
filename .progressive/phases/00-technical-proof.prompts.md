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

### pm-01-r1
Task: PM-01 — Kanban работ проекта
Status: DONE
Freshness: CHECKED 14.11.2026
Source: решение пользователя 14.11.2026 («Да, начинаем PM-01»); MVP-SPEC §11.1 PLAN-02, PLAN-03, PLAN-06
Supersedes: NONE

#### Request
```text
Я б сосредаточился бы сперва созданием mast-have функции. Такие как Kabnab доски, Whiteboard и другие.
Своего рода clickup и yougile. → Да, начинаем PM-01 (раньше TP-02).
```

#### Prompt
```text
Доска работ проекта на /av/board (Vue 3 + frappe-ui), данные — штатные задачи ERPNext (Task), без копий.
Колонки — DocType AV Work Stage (настройка, ARC-02) с базовым набором H: Запланировано → Готово к работе →
В работе → На проверке → Завершено; этап сопоставлен статусу ERPNext. Карточка: название, проект,
ответственные, срок, помещение/система, причина блокировки. Фильтры: проект, исполнитель, помещение/система, срок.
Перемещение: drag-and-drop и меню/клавиатура; решение только на сервере (pm_api.move_task):
право записи, участие в проекте, открытые зависимости, блокировка, закрытая задача, конфликт версии.
Отказ — стабильный код, текст на клиенте; карточка остаётся на месте. Доска показывает только проекты,
где пользователь участник (Project.users) или задачи, назначенные ему; System Manager / Projects Manager — все.
Синтетические задачи для учебного проекта — в demo.seed. Frappe-тесты на переходы и права.
Не входит: глобальное ограничение прав Task/Project в Desk (требует согласия пользователя), timeline,
«Мои задачи», доска сделок, whiteboard, realtime-обновление.
```

#### Freshness check
14.11.2026: ERPNext 16 Task даёт Projects User чтение/запись всех задач без учёта участия в проекте (task.json);
статус Overdue выставляет планировщик (set_tasks_as_overdue). frappe-ui 1.2.0 без Kanban-компонента.
Параллельная сессия правит sales_api.py, api.ts, ru.ts — PM-01 живёт в отдельных файлах.

#### Current checkpoint
Выполнено. Изменения в рабочем дереве не закоммичены.

#### Outcome / evidence
- 14.11.2026: `npm run build` PASS; `manage.ps1 up`, `seed` дважды PASS; `manage.ps1 test` 37/37 PASS (16 новых в test_pm_api.py).
- Браузер под PM: доска, отказ `blocked` с причиной, перенос в «В работе» → в базе `in_progress` / `Working`. Drop проверен событиями DragEvent из JS; жест мышью и узкий экран NOT RUN.
- Остаточный риск: права Task/Project в Desk не ограничены участием (поведение ERPNext); глобальное правило ждёт решения пользователя.
- Исправлено по ходу: `assign_to.add` в Frappe 16.55.1 не принимает `ignore_permissions`; `useCall.submit` возвращал null — ответ читается из `move.data`; кнопка меню перемещения — через `button` у Dropdown.

### pm-02-r1
Task: PM-02 — «Мои задачи»
Status: DONE
Freshness: CHECKED 14.11.2026
Source: поручение пользователя 14.11.2026 («PM-02 «Мои задачи»»); MVP-SPEC §11.1 PLAN-05, PLAN-03, PLAN-06; research/07
Supersedes: NONE

#### Request
```text
PM-02 «Мои задачи»
```

#### Prompt
```text
Страница /av/my-tasks (Vue 3 + frappe-ui) поверх штатных задач ERPNext. Вкладки «Назначены мне» (открытый ToDo
на пользователя) и «Поручено мной» (ToDo, назначенный пользователем другим). Группы по сроку считает сервер
по своей дате: Просрочено / Сегодня / На этой неделе (до воскресенья) / Позже / Без срока. Видимость как у доски
PM-01. Из строки: «следующий этап» и меню этапов через pm_api.move_task (те же проверки и коды отказа).
Фильтры: проект, поиск по названию/помещению/системе. Пустые состояния и узкий экран. Frappe-тесты.
Не входит: «Чужие задачи» руководителя, личные/приватные списки, уведомления, глобальные права Desk.
```

#### Freshness check
14.11.2026: назначение в ERPNext — ToDo (allocated_to, assigned_by, status Open/Closed/Cancelled); useCall frappe-ui 1.2.0
принимает params-функцию и refetch. Параллельных сессий нет.

#### Current checkpoint
Выполнено. Изменения в рабочем дереве не закоммичены.

#### Outcome / evidence
- 14.11.2026: `npm run build` PASS; `manage.ps1 up` PASS; `manage.ps1 test` 47/47 PASS (10 новых в test_my_tasks.py); ruff PASS.
- Браузер под PM: группы, перевод «следующий этап», отказ `blocked` с причиной, пустая вкладка «Поручено мной», ширина 375 px без выхода за край.
- Исправлен хрупкий тест PM-01 (требовал работу в каждой колонке учебного проекта).
