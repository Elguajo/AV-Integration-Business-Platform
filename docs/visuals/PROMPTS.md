# Промпты концептуальных макетов

Дата: 11 ноября 2026 года. Способ: встроенный инструмент ImageGen (`image_gen`), без CLI/API-скриптов. Изображения иллюстрируют возможный интерфейс; дизайн и данные не являются результатом запуска продукта. Основание: [MVP-SPEC.md](../../MVP-SPEC.md), разделы 3, 11, 13 и 14. Макеты не добавляют требований к V1.

## Рабочее место PM

```text
Use case: ui-mockup. Asset type: a crisp high-fidelity concept screenshot for the GitHub README of an AV integration business platform. This is a FUTURE PRODUCT CONCEPT, not a screenshot of implemented software. All text Russian, accurately spelled Cyrillic. Flat front-facing desktop UI, landscape 16:10, high resolution, large legible typography. Product identity is temporary plain text "AV Platform". Calm precise engineering workplace: warm white canvas, graphite text, subtle gray dividers, dark graphite sidebar, restrained teal accents, amber blockers. No glossy effects, no gradients, no stock imagery, no charts without purpose, no floating devices, no perspective, no background staging. Strong alignment, generous but efficient spacing, information-rich professional desktop application. Use status text plus color, not color alone. Small top-right badge "Концепт · учебные данные". Sidebar links: "Обзор", "Продажи", "Проекты", "Оборудование", "Команда", "Финансы", "Транспорт". Topbar includes search and role "PM". Make major headings and numbers clear at README display width. No claims of real data or actual implementation.
Primary request: show the project manager workspace for a single AV project. Main heading "Конференц-зал · P1", subtitle "Проект / Исполнение", room chips "Зал A" and "Зал B". Select "Проекты" in sidebar. Main tabs "Обзор", "План", "Kanban", "BOM", "Документы", "Испытания". Selected tab "Обзор".
Top row of four restrained summary cells: "Договор" with "16 000 USD"; "Прогноз затрат" with "12 500 USD"; "Прогноз маржи" with "3 500 USD"; "Блокировки" with "2". Small supporting note "AC 6 800 · OC 2 200 · ETC 3 000 · Риск 500". Never label this as completed profit.
Dominant middle area: "План проекта" horizontal timeline, dates "9–20 ноября", five aligned rows with labels "Проектирование", "Закупка", "Монтаж", "Программирование", "Испытания"; visible overlapping bars, one dependency, milestone diamond "Сдача". Slim vertical today line. Right-hand panel "Требует внимания": amber item "Сеть заказчика не готова", responsible "PM", next action "Подтвердить готовность"; second item "Ожидаем поставку DSP", responsible "Закупщик", next action "Уточнить ETA". Distinguish external readiness, delivered gear, deployed configuration, and verified results.
Lower area "Работы команды": compact Kanban with three columns "К выполнению", "В работе", "Проверка". Four readable task cards total: "Выпустить схему", "Собрать рэк", "Настроить DSP", "Проверить сценарии". Role tags "Проектировщик", "Техник", "Программист", "Наладчик". Selected task "Настроить DSP" includes "CFG2 · Зал A". Footer "Обновлено сегодня · Источники и история доступны". Keep structure coherent and visually clean; do not add artificial overall project completion percentages or false acceptance success.
```

## Транспортные расходы

```text
Use case: ui-mockup. Asset type: a crisp high-fidelity concept screenshot for the GitHub README of an AV integration business platform. This is a FUTURE PRODUCT CONCEPT, not a screenshot of implemented software. All text Russian, accurately spelled Cyrillic. Flat front-facing desktop UI, landscape 16:10, high resolution, large legible typography. Product identity is temporary plain text "AV Platform". Calm precise engineering workplace: warm white canvas, graphite text, subtle gray dividers, dark graphite sidebar, restrained teal accents, amber blockers. No glossy effects, no gradients, no stock imagery, no charts without purpose, no floating devices, no perspective, no background staging. Strong alignment, generous but efficient spacing, information-rich professional desktop application. Use status text plus color, not color alone. Small top-right badge "Концепт · учебные данные". Sidebar links: "Обзор", "Продажи", "Проекты", "Оборудование", "Команда", "Финансы", "Транспорт". Topbar includes search and role "PM". Make major headings and numbers clear at README display width. No claims of real data or actual implementation.
Primary request: show the company's transport expenses workspace, separate full-size desktop screenshot in same design language. Select "Транспорт" in sidebar. Main heading "Транспортные расходы", subtitle "Такси и заправка служебных автомобилей". Date filter "Ноябрь 2026", other filter chips "Все проекты", "Все сотрудники", "Все автомобили". Primary action "+ Добавить расход".
Top summary row EXACT values: "Такси" "100 USD"; "Топливо" "250 USD"; "Всего признано" "350 USD"; "На проверке" "30 USD". Clear explanatory line "Оплата и возмещение учитываются отдельно от затрат".
Large central expense table, spacious with EXACT columns "Дата", "Категория", "Назначение", "Распределение", "Сумма", "Статус".
Four rows:
"11 ноя" | "Такси" | "Выезд на объект" | "P1" | "100 USD" | "Признано"
"10 ноя" | "Топливо" | "Служебный автомобиль 01" | "P1: 120 · P2: 80" | "200 USD" | "Признано"
"09 ноя" | "Топливо" | "Общая заправка" | "Общие расходы" | "50 USD" | "Признано"
"11 ноя" | "Такси" | "Поездка на согласование" | "Не распределено" | "30 USD" | "На проверке"
Bottom left section "Распределение признанных затрат" with three simple horizontal bars correctly scaled "P1 — 220 USD", "P2 — 80 USD", "Общие — 50 USD". These sum to 350, not 380.
Bottom right a detail card "Возмещение сотруднику" for the 100 USD taxi: "Расход 100 USD", "Возмещено 40 USD", "Осталось 60 USD". Note "Возмещение не увеличивает затраты повторно". Small "Чек" attachment indicator. No GPS map, no fabricated vehicle telemetry, no fuel efficiency metrics, no chart implying fuel purchase equals consumption. Currency all USD synthetic. Make the financial distinction legible, calm, and understandable.
```

## Уточнение роли на макете транспортных расходов

После проверки исходного макета роль PM заменена на «Финансы»: общий реестр по нескольким проектам доступен финансовому ответственному. Финальный файл: `transport-expenses-concept.png`. Точечное редактирование выполнено встроенным ImageGen; остальные данные сохранены.

```text
Edit the most recent transport expenses concept screenshot only. Change exactly the top bar role selector text "PM" to "Финансы" (Russian for Finance), making the selector slightly wider if needed within its existing area. Finance role is necessary because this screen shows company-wide expenses from multiple projects; a project manager must not have this access. Preserve every other element, all values, table, type, spacing, colors, sidebar, concept badge and image dimensions unchanged. Do not add or remove data. Cyrillic role text spelled exactly "Финансы".
```
