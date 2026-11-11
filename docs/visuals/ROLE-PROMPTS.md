# Промпты ролевых рабочих мест

Дата: 11 ноября 2026 года. Созданы встроенным ImageGen с существующим [макетом PM](project-workspace-concept.png) только как визуальным референсом. Все сведения учебные. Основание: [MVP-SPEC.md](../../MVP-SPEC.md), разделы 3–4, SAL, REL, FLD и CFG. Макеты показывают разные роли и этапы; они не изображают одновременное состояние одного проекта и не добавляют требований к V1.

## Sales Manager

Файл: `sales-manager-workspace-concept.png`.

```text
Use case: ui-mockup. High-fidelity FUTURE product concept screenshot for a Russian-language AV integration business platform README. The provided image is a STYLE REFERENCE ONLY: retain its AV Platform identity, dark graphite navigation, white work surface, teal action accents, amber warnings, subtle gray dividers, precise readable Cyrillic typography, spacing and professional engineering feel. Create a completely NEW role-specific workspace, not a PM dashboard reskin. Flat front-facing UI, crisp high resolution. No device frames, perspective, photos as decoration, gradients or marketing copy. Every datum is synthetic; compact badge "Концепт · учебные данные". Display status in words as well as color. Prioritize readable work content, real actions and role boundaries. Do not copy the reference financial KPIs or its PM sidebar. No real people, customers, credentials or external URLs. No overall project completion percentage.
Landscape desktop 16:10. Top bar role selector "Sales Manager". Sidebar exactly "Мой день", "Мои сделки" selected, "Клиенты", "Предложения", "Передачи PM". Do NOT show global finance or company profit.
Main heading "Мои сделки". Under heading quick filters "Мои", "Нужен следующий шаг", "Ожидаем инженера", plus "+ Сделка".
Main left two-thirds: pipeline Kanban with three visible columns "Проработка", "Предложение", "Переговоры". Four substantive cards total. "Переговорная B" with "Обследование · 12 ноября" and "Бюджет уточняется" in Проработка. "Малый зал" with "Ждём расчёт инженера" in Проработка. "Учебный офис" with "КП Q1 · Черновик" in Предложение. Selected card in Переговоры: "Конференц-зал", "Учебный клиент", "КП Q2 · 16 000 USD", "Следующий шаг: обсудить КП · 12 ноября". Pipeline amounts are potential proposals, not contract revenue.
Right one-third detail panel for selected deal: heading "Конференц-зал"; tabs "Контакт", "КП и условия", "История". Version chips "Q1 · Архив", "Q2 · Отправлено". Commercial details "Основной состав: 16 000 USD", "Опции: отдельно", "Сроки: на согласовании". Next action box "Обсудить состав и сроки", "12 ноября · Sales". Engineer request status "Техническая проверка завершена". Three distinct handover statuses "Решение клиента: ожидается", "Разрешение старта: не получено", "Аванс: не подтверждён". A disabled button "Передать PM" and clear hint "Нужно основание согласования клиента". Enabled secondary action "Создать версию Q3". Bottom small task strip "Сегодня" with "Подтвердить время обследования" and "Запросить решение по Q2". Emphasize personal execution, not managerial statistics.
```

## Presales Engineer

Файл: `presales-engineer-workspace-concept.png`.

```text
Use case: ui-mockup. High-fidelity FUTURE product concept screenshot for a Russian-language AV integration business platform README. The provided image is a STYLE REFERENCE ONLY: retain its AV Platform identity, dark graphite navigation, white work surface, teal action accents, amber warnings, subtle gray dividers, precise readable Cyrillic typography, spacing and professional engineering feel. Create a completely NEW role-specific workspace, not a PM dashboard reskin. Flat front-facing UI, crisp high resolution. No device frames, perspective, photos as decoration, gradients or marketing copy. Every datum is synthetic; compact badge "Концепт · учебные данные". Display status in words as well as color. Prioritize readable work content, real actions and role boundaries. Do not copy the reference financial KPIs or its PM sidebar. No real people, customers, credentials or external URLs. No overall project completion percentage.
Landscape desktop 16:10. Top bar role "Presales Engineer". Sidebar "Мои запросы", "Требования", "Решения" selected, "BOM", "Документы". No global financial navigation or dashboard metrics.
Main heading "Техническое решение · Конференц-зал"; breadcrumb "Запрос Sales → Проработка". Teal primary button "Сохранить ревизию"; secondary "Ответить Sales". Current chips "BOM E3 · Черновик", "Зал A".
Upper horizontal requirements strip: "Видеоконференция", "Локальная презентация", "Управление с панели". Amber question "IT: подтвердить VLAN", owner "PM".
Central majority: "Фрагмент BOM · E3" real engineering table with columns "Позиция", "Кол-во", "Интерфейсы", "Проверка". Four rows:
"Дисплей M" | "2 шт." | "HDMI / LAN" | "Проверено"
"DSP" | "1 шт." | "Dante / USB" | "Уточнить лицензию"
"Панель управления" | "1 шт." | "PoE / LAN" | "Проверить питание"
"Крепление" | "2 шт." | "VESA" | "Проверено".
No prices in this particular engineer permission set.
Right inspector selected DSP: "Совместимость", checklist "USB для конференций — проверено", "Лицензия Dante — уточнить", "Драйвер управления — версия 1.2", "Труд: программирование — 8 ч". Warning "Не выпускать DSP до проверки лицензии". Source document chip "Схема S-02 · Rev B".
Lower panel "Проверенное решение → Sales": items "Сценарии", "Состав и альтернативы", "Нормы работ", "Допущения и риски". Status "Есть открытые вопросы". Separate engineering release area "Технический выпуск" with checked items "Дисплеи и крепления"; button "Передать проверенные позиции PM". Explicit visible footnote "Техническая проверка не разрешает закупку. Разрешение — PM." No button allowing engineer to place an order, no implied approval of unresolved DSP.
```

## Монтажник

Файл: `installer-workspace-concept.png`.

```text
Use case: ui-mockup. High-fidelity FUTURE product concept screenshot for a Russian-language AV integration business platform README. The provided image is a STYLE REFERENCE ONLY: retain its AV Platform identity, dark graphite navigation, white work surface, teal action accents, amber warnings, subtle gray dividers, precise readable Cyrillic typography, spacing and professional engineering feel. Create a completely NEW role-specific workspace, not a PM dashboard reskin. Flat front-facing UI, crisp high resolution. No device frames, perspective, photos as decoration, gradients or marketing copy. Every datum is synthetic; compact badge "Концепт · учебные данные". Display status in words as well as color. Prioritize readable work content, real actions and role boundaries. Do not copy the reference financial KPIs or its PM sidebar. No real people, customers, credentials or external URLs. No overall project completion percentage.
Portrait mobile screenshot 9:18, full edge-to-edge app, no physical phone frame. Preserve reference design language in a compact mobile layout. Clearly large touch targets, readable text, bottom navigation. Role at top "Монтажник". Header brand "AV Platform", smaller badge "Концепт · учебные данные". Show a single task workspace, no financial data or PM dashboard.
Top back navigation "Мои задания"; heading "Установить DSP". Context "Конференц-зал · Зал A", "Рэк R1 · Место U08", task ID "TASK-014". Small status "В работе". Assigned to "Мой пользователь"; approving role "Ведущий техник".
Prominent short instruction card "Результат": "Закрепить DSP, подключить и промаркировать кабели. Приложить фото." Technical preconditions box: "Монтаж разрешён PM"; amber separate text "Сеть не готова: наладка позже". Never present network as ready or project as accepted.
A released document row with file icon "Монтажная схема · Rev B", status "Выпущена", button "Открыть". Equipment section "Назначенная единица" with "DSP-DEMO-01", "Комплект: получен", small "Сканировать QR". Use this synthetic serial only.
Simple checklist: checked "Сверил устройство и схему", unchecked "Крепление и маркировка", unchecked "Фото результата". Clear photo attachment tile "+ Добавить фото", no fabricated completed photo.
A compact time entry "Мои часы" with "1 ч 20 мин" and edit icon, no wage rate. Secondary action "Сообщить о проблеме". Draft status "Результат ещё не отправлен". Bottom sticky main button "Передать на проверку". Bottom nav "Задания" selected, "Сканер", "Мой профиль". Do not add client sign-off or acceptance button. This is online field input with explicit unsent draft, not offline sync. Fit all key content without microtype; trim unimportant decoration first.
```

## Программист

Файл: `programmer-workspace-concept.png`.

```text
Use case: ui-mockup. High-fidelity FUTURE product concept screenshot for a Russian-language AV integration business platform README. The provided image is a STYLE REFERENCE ONLY: retain its AV Platform identity, dark graphite navigation, white work surface, teal action accents, amber warnings, subtle gray dividers, precise readable Cyrillic typography, spacing and professional engineering feel. Create a completely NEW role-specific workspace, not a PM dashboard reskin. Flat front-facing UI, crisp high resolution. No device frames, perspective, photos as decoration, gradients or marketing copy. Every datum is synthetic; compact badge "Концепт · учебные данные". Display status in words as well as color. Prioritize readable work content, real actions and role boundaries. Do not copy the reference financial KPIs or its PM sidebar. No real people, customers, credentials or external URLs. No overall project completion percentage.
Landscape desktop 16:10. Role selector "Программист". Sidebar "Мои задачи", "Сценарии", "Конфигурации" selected, "Развёртывания", "Проверки", "Документы". No money, staffing dashboard, billing or IDE/code editor.
Main heading "Конфигурации · Конференц-зал". Subtitle "Зал A · Control / GUI / DSP". Header action "Оформить выпуск CFG2", secondary "Открыть источник". Current task small "Настроить сценарий видеоконференции".
Top explicit separated state strip: "Исходники: v0.2" / "CFG2: подготовлена" / "На объекте: CFG1" / "Проверки на объекте: BLOCKED". These are distinct states; preparing a release must not claim deployment.
Large main left panel "Состав CFG2 · Manifest": readable table columns "Компонент", "Версия", "Основание":
"Control" | "v0.2" | "Источник: tag control-v0.2"
"GUI" | "v0.3" | "Макет GUI-03"
"DSP" | "preset 02" | "DSP-DEMO-01"
"Драйвер" | "1.2" | "Матрица совместимости"
"Схема" | "Rev B" | "S-02".
Right panel "Контекст и ограничения": "Среда: стенд", "Сеть объекта: VLAN ожидается", "Владелец: PM", "Известное ограничение: нет доступа к сети объекта". No password or secret field.
Bottom left "Проверки сборки": two explicit rows "FAT · CFG2 · стенд" status "PASS · 4/4" and "Проверка · CFG2 · объект" status "BLOCKED". Text "Стендовые результаты не подтверждают готовность на объекте".
Bottom right "История развёртываний": "CFG1 → Зал A · 10 ноября", "Backup CFG1 · сохранён". Disabled secondary button "Записать развёртывание CFG2" with hint "После выпуска и фактической загрузки". No one-click magic AV programming. Small note "Откат фиксируется новым развёртыванием". Clear practical workbench with release metadata and task context, not a PM overview.
```
