# Источники и границы доказательств

Дата исследования: 5 ноября 2026 года. Ссылки проверялись веб-поиском и чтением доступных страниц. Источники ниже — официальные страницы организаций, поставщиков и их документация; отзывы агрегаторов и обсуждения форумов не использованы как доказательство функций.

Публичная документация подтверждает описанный механизм, а не качество работы, доступность в любом тарифе, совместимость с компанией или отсутствие других функций. Цены, рыночные доли и количество звёзд GitHub не используются для выбора основы.

## 1. Материалы проекта и слова пользователя

Четыре ранних черновика удалены при очистке папки по запросу пользователя после переноса выводов в исследование. Их названия ниже сохранены для истории происхождения выводов; AV-WORKFLOW.md остаётся в проекте.

| Источник | Что из него использовано | Ограничение |
|---|---|---|
| `Sample.md` (удалённый черновик) | Гипотеза перехода к Frappe/ERPNext и отдельному AV app | Архитектурное предложение; практических результатов нет |
| `sample-1.md` (удалённый черновик) | Plane как UI-ориентир | Подробного анализа Plane нет; численные показатели популярности не перепроверялись и не используются |
| `refrence-repo.md` (удалённый черновик) | Перечень бизнес-сущностей и AV-надстройки | Описательная гипотеза, не подтверждение готовой реализации |
| `architecture-sample.md` (удалённый черновик) | Project, AV System, deployment, commissioning, dashboard, путь внутреннего продукта к SaaS | Финансовый пример и линейный lifecycle требуют уточнений |
| [AV-WORKFLOW.md](../AV-WORKFLOW.md) | 16 этапов, четыре направления, FAT, integration, acceptance, documentation/training, support | Нет исходного изображения и доказательств оценки покрытия 60–70%; это не наблюдённый процесс компании |
| Сообщения пользователя в текущем чате | Собственный веб-продукт по опыту SI/Jetbuilt; сначала своя компания, возможная продажа позднее | Страна, масштаб и текущие системы пока неизвестны |

## 2. Основные референсы: D-Tools SI

| № | Источник | Что подтверждает |
|---|---|---|
| SI1 | [System Integrator Overview](https://docs.d-tools.com/en/articles/9207945-system-integrator-overview) | Связь оценки, проектирования и управления; каталог, закупки, timesheets и отчёты |
| SI2 | [Creating Change Orders](https://docs.d-tools.com/en/articles/9216319-creating-change-orders) | Изменения утверждённых позиций через CO, External/Internal, non-billable |
| SI3 | [Creating Purchase Orders](https://docs.d-tools.com/en/articles/9224095-creating-purchase-orders) | Заказы на несколько проектов; частичное/полное получение |
| SI4 | [Managing Tasks in Mobile Install](https://docs.d-tools.com/en/articles/9224019-managing-tasks-in-mobile-install) | Полевые задачи, picked/installed и данные конкретных устройств |
| SI5 | [Updating Project Data from Tasks and Purchase Orders](https://docs.d-tools.com/en/articles/9459201-updating-project-data-manually-from-tasks-and-purchase-orders) | Обновление проектных полей из исполнения и PO; настройки и распределение серийных данных |
| SI6 | [D-Tools SI API Overview](https://docs.d-tools.com/en/articles/9225625-d-tools-si-api-overview) | SI-specific API через облачного посредника/очередь; экспорт и асинхронное применение данных |
| SI7 | [Solutions](https://docs.d-tools.com/en/articles/9216152-solutions) | Иерархия locations и список systems; группировка позиций |
| SI8 | [SI Product Page](https://www.d-tools.com/system-integrator) | Позиционирование SI как платформы для интеграционных проектов; дополнительный контекст |

SI6 прямо отличает API SI от D-Tools Cloud. В исследовании эти продукты не объединяются в одну реализацию. Статьи разных дат описывают механизмы; конкретная версия установленного у пользователя SI неизвестна, наличие такой установки не предполагается.

## 3. Основные референсы: Jetbuilt

| № | Источник | Что подтверждает |
|---|---|---|
| J1 | [Install Platform](https://help.jetbuilt.com/en/articles/2286554-install-platform) | Задачи от item, назначения, JetbuiltGO, обзор времени и проектов |
| J2 | [Stock](https://help.jetbuilt.com/en/articles/5574265-stock) | QR, приёмка, перемещения, серийные номера и выделение проекту |
| J3 | [Project Stages Explained](https://help.jetbuilt.com/en/articles/791923-project-stages-explained) | Пример стадий и optional Post-Engineering; дополнительный контекст |
| J4 | [How to Turn On the Engineering/Scrub Stage](https://help.jetbuilt.com/en/articles/5996511-how-to-turn-on-the-engineering-scrub-stage) | Pre/Post engineering, роли и отдельные reference versions |
| J5 | [How to Use the Engineering Scrub Stage](https://help.jetbuilt.com/en/articles/6004508-how-to-use-the-engineering-scrub-stage) | Swap, Engineering Release, сравнение версий и Project Manager Release |
| J6 | [Comparing Install Budget vs. Actual](https://help.jetbuilt.com/en/articles/6249944-comparing-install-budget-vs-actual) | План и фактическое время по видам труда; различие времени и выполнения задач |
| J7 | [Stock: Alternate Workflow](https://help.jetbuilt.com/en/articles/5905379-stock-alternate-workflow) | Ведение stock при неиспользовании Jetbuilt для PO |

По этим источникам не делается вывод об отсутствии commissioning, прогнозов или иных функций, которые не рассмотрены подробно. Их глубина остаётся вопросом дополнительного изучения.

## 4. Отраслевой процесс и качество

| № | Источник | Что подтверждает | Ограничение |
|---|---|---|---|
| A1 | [AVIXA: Audiovisual Systems Performance Verification](https://www.avixa.org/resources/standards/av-systems-performance-verification) | Определение проверяемого объёма, времени, критериев/метрик и отчётности | Изучена публичная аннотация; полный стандарт не использовался |
| A2 | [AVIXA: Documentation Requirements](https://www.avixa.org/resources/standards/documentation-requirements-for-audiovisual-systems) | D401.01:2023: требования к документации, ответственность, отслеживание передачи | Не заявляется соответствие продукта стандарту |
| A3 | [AQAV](https://www.aqav.org/) | Design/Engineering, Staging, Commissioning и System Acceptance в программе качества | Публичное описание, не сертификационная проверка |
| A4 | [NSCA: Workforce, 18 February 2025](https://www.nsca.org/nsca-news/tips-integrators-retain-top-talent-nsca-news-nsca/) | Контекст дефицита технических специалистов и стоимости труда | Североамериканский контекст не переносится в количественные оценки для компании пользователя |

Собственные шаблоны проверок, контрольные точки, пороги готовности и названия статусов в отчёте — аналитические предложения. Ни AVIXA, ни AQAV не цитируются как источник универсального workflow из 16 последовательных стадий.

## 5. ERPNext/Frappe

| № | Источник | Что подтверждает |
|---|---|---|
| F1 | [Project Profitability](https://docs.frappe.io/erpnext/project-profitability) | Связь проекта с sales/purchase transactions и учётом доходов/расходов |
| F2 | [Project Costing](https://docs.frappe.io/erpnext/project-costing) | Timesheet, Activity Cost, ставки и стоимость времени |
| F3 | [Project](https://docs.frappe.io/erpnext/project) | Стандартные project costing/billing поля и источники некоторых сумм |
| F4 | [Serial Number](https://docs.frappe.io/erpnext/serial-no) | Учёт отдельных сериализованных единиц и связь со складскими операциями |
| F5 | [Asset](https://docs.frappe.io/erpnext/asset) | Капитализация и амортизация активов компании |
| F6 | [Purchase Receipt](https://docs.frappe.io/erpnext/purchase-receipt) | Физическое получение и обработка частичных поставок |
| F7 | [Landed Cost Voucher](https://docs.frappe.io/erpnext/stock-transactions-landed-cost-voucher) | Распределение дополнительных относимых расходов в складской оценке |
| F8 | [Hooks](https://docs.frappe.io/framework/user/en/python-api/hooks) | Расширения поведения, события, fixtures; зависимость отдельных hooks от версии |
| F9 | [Database Migrations](https://docs.frappe.io/framework/user/en/database-migrations) | Изменения DocTypes и механизм миграций приложения |
| F10 | [REST API](https://docs.frappe.io/framework/user/en/api/rest) | API для DocTypes; наличие доступа не равно готовой бизнес-интеграции |
| F11 | [Sites](https://docs.frappe.io/framework/user/en/basics/sites) | Multitenancy и отдельная база для site |
| F12 | [Installation](https://docs.frappe.io/framework/user/en/installation) | Поддерживаемые ОС, WSL для Windows и зависимости по веткам |
| F13 | [Attachments](https://docs.frappe.io/framework/user/en/desk/attachments) | Связь доступа к вложениям с чтением документа |
| F14 | [frappe/frappe](https://github.com/frappe/frappe) | Официальный репозиторий framework, MIT |
| F15 | [frappe/erpnext](https://github.com/frappe/erpnext) | Официальный репозиторий ERPNext, GPL-3.0 |

Документация F3 содержит изложение агрегатов и формул. В исследовании они не копируются как проверенная формула проектной прибыли: результат нужно сверять с конкретной версией приложения и выбранным учётом. Предлагаемый EAC — наша прозрачная управленческая модель, а не обещание штатной функции ERPNext.

Поддержка PostgreSQL на уровне framework не используется как доказательство пригодности ERPNext на PostgreSQL. Для первого кандидата рассматривается документированная MariaDB-основа; реальная версия и конфигурация ещё не выбраны.

## 6. Дополнительные продуктовые ориентиры

| № | Источник | Что подтверждает |
|---|---|---|
| C1 | [D-Tools Cloud Projects](https://docs.d-tools.cloud/en/collections/861695-projects) | Проектные задачи, статусы, закупка, inventory allocation, изменения и время |
| C2 | [D-Tools Cloud: Viewing job costing](https://docs.d-tools.cloud/en/articles/10470382-viewing-job-costing) | Budget vs actual по фазам/труду и доступ к стоимости; относится к Cloud |
| C3 | [ProjX360 Project Management](https://projx360.com/features/project-management) | Проектные стадии, задачи, документы, время и work orders |
| C4 | [ProjX360 Inventory Management](https://projx360.com/features/inventory-management) | Склады, серийный/штрихкодовый учёт, распределение и перемещения |
| C5 | [Q360 for AV Companies](https://solutions360.com/by-industry/av/) | AV-позиционирование, проекты, оборудование и сервис |
| C6 | [Q360 Projects](https://helpv24.q360.com/docs-inline/projects/) | Отчёты по прибыли, Project Revenue / Cost Forecast и WIP; справка версии, указанной в URL |
| C7 | [XTEN-AV X-PRO Knowledge Base](https://knowledgebase.xtenav.com/en-us/category/x-pro-installation-cyaw02/) | Документация задач, проектных операций и статусов inventory |
| C8 | [Odoo 19 Project Profitability](https://www.odoo.com/documentation/19.0/applications/services/project/project_management/project_profitability.html) | Проектная аналитика и привязка записей к проекту/analytic account |
| C9 | [Odoo 19 Field Service Worksheets](https://www.odoo.com/documentation/19.0/applications/services/field_service/worksheets.html) | Формы для выполнения и отчётности выездных работ |

C8 получен через содержимое поисковой выдачи официальной документации: прямое открытие страницы несколько раз завершалось тайм-аутом. Поэтому по нему не делается подробный вывод о поведении продукта или обязательствах по незакрытым PO. Анализ конкретной редакции и установленной версии Odoo не проводился.

## 7. Открытые вопросы с наибольшим влиянием

| Вопрос | Почему влияет на решение | Как получить ответ |
|---|---|---|
| Где ведутся заказы, склад и бухгалтерия? | Определяет границы ERPNext и интеграций | Инвентаризация инструментов и один реальный документ каждого типа |
| Какие проекты типичны и сколько их одновременно? | Определяет шаблоны, роли, масштаб портфеля | Выборка текущих и закрытых проектов |
| Где чаще всего теряются деньги и дни? | Определяет приоритет первой версии | Ретроспектива конкретных событий с подтверждениями |
| Как считается себестоимость? | Определяет AC, OC, прогноз и сверку | Разбор с финансовым ответственным |
| Насколько нужна работа без связи? | Может изменить устройство полевого приложения | Наблюдение на объектах |
| Как принимаются изменения и частичные объёмы? | Определяет права, версии, сдачу и выручку | Договоры, переписка решений и примеры актов/протоколов |
| Какой опыт SI/Jetbuilt есть у команды? | Позволяет отделить нужные привычки от неудобств, которые стоит исправить | Наблюдение работы и разбор конкретных операций |
| Есть ли спрос у других компаний? | Определяет будущую коммерческую упаковку | Внешние интервью и пилоты после внутреннего результата |

Ни один открытый вопрос не отменяет согласованную цель собственной разработки. Он уточняет техническую основу, глубину модулей и последовательность проверки.

## 8. Дополнительная проверка механизмов 5 ноября 2026 года

Результаты чтения конкретных операций и границы выводов — в [05-mechanisms-and-decisions.md](05-mechanisms-and-decisions.md). Повторно прочитаны SI2–SI6, J2/J5–J7, F1/F2/F6 и A1/A2. Страницы открывались как официальная документация; это не испытание продукта и не проверка API. Ниже новые стабильные коды, продолжающие исходный реестр.

| ID | Официальный источник | Предмет подтверждения / ограничение |
|---|---|---|
| SI9 | [Marking a Project as Approved](https://docs.d-tools.com/en/articles/10917780-marking-a-project-as-approved) | Полное/частичное утверждение, revision и pending CO; не наш договорный порядок |
| SI10 | [Proposal](https://docs.d-tools.com/en/articles/9220822-proposal) | Состав/настройки клиентского отчёта; не доказательство полноценной CRM в SI |
| SI11 | [Managing Purchase Orders](https://docs.d-tools.com/en/articles/9224100-managing-purchase-orders) | Item Receipts, количество партии и идентификаторы устройств |
| SI12 | [Users](https://docs.d-tools.com/en/articles/9208074-users) | Различие пользователя, ресурса, роли и permission group |
| SI13 | [Phases and Labor Types in v20](https://docs.d-tools.com/en/articles/9225455-phases-and-labor-types-in-v20) | Разделение этапа и типа труда в описанной версии; не последний номер релиза |
| J8 | [Quantity Columns in Stock](https://help.jetbuilt.com/en/articles/8417991-quantity-columns-in-stock-and-allocation-vs-assignment) | Различие allocation/assignment и ограничение количеств |
| J9 | [Returning to Stock](https://help.jetbuilt.com/en/articles/8548415-unassigning-un-allocating-items-in-a-project-returning-to-stock) | Снятие назначения/резерва; не возврат денег поставщиком |
| J10 | [Uninstalling Items from Final Locations](https://help.jetbuilt.com/en/articles/11132570-uninstalling-items-from-final-locations) | Демонтаж с сохранением назначения и ограничение общего QR для bulk |
| J11 | [Accurate Cost in Stock Inventory Report](https://help.jetbuilt.com/en/articles/7039221-accurate-cost-in-stock-inventory-report) | Источники Cost в этом отчёте; историческая себестоимость поставки этим не доказана |
| J12 | [User Permission Breakdown](https://help.jetbuilt.com/en/articles/4381821-user-permission-breakdown) | Полномочия и доступ к стоимости через разные области; зависит от редакции |
| F16 | [Stock Reservation](https://docs.frappe.io/erpnext/stock-reservation) | Штатный сценарий Sales Order/Pick List; проектный AV-reservation требует проверки |
| F17 | [Serial and Batch Bundle](https://docs.frappe.io/erpnext/serial-and-batch-bundle) | Механизм складских идентификаторов, введённый в v15; реализация выбранной версии не проверена |

В SI6 дополнительно прочитан раздел v24 о проверке времени публикации при подтверждении импорта. Это документированная защита от пропуска более новой публикации; наличие её в конкретной установке неизвестно. В F6 уточнено разделение физического приёма и supplier payable; управленческая точка AC по-прежнему выбирается отдельно.

Страница [SI Approving the Quote](https://docs.d-tools.com/en/articles/10131420-approving-the-quote) и материалы D-Tools Cloud о воронке были обнаружены поиском. Они не используются как доказательство единой CRM-модели SI: Mobile Quote и Cloud нельзя смешивать с основной реализацией SI. Состав Sales в V1 — подтверждённое направление пользователя и наше продуктовое предложение.

## 9. Новые материалы и происхождение требований

| Материал / свидетельство | Что изменяет | Ограничение |
|---|---|---|
| Уточнение пользователя о каждом этапе и отдельных учётных записях Sales/инженеров/проектировщика/программиста | Минимальные продажи и рабочие места включены в V1 | Не раскрывает реальную оргструктуру и полномочия |
| Отдельное уточнение о техниках/монтажниках | Их входы, информация и полевые действия обязательны | Условия объектов/связи неизвестны |
| Осмотр рабочей папки | Реальных проектных данных нет; есть Git без коммитов | Частные данные вне папки не разыскивались |
| [MVP-SPEC.md](../MVP-SPEC.md) | Предварительные правила, инварианты, сценарии и открытые решения | T1 синтетический, требования H ещё не подтверждены в поле |
| [06-real-project-validation.md](06-real-project-validation.md) | План проверки одного проекта | Интервью/разбор ещё не проведены |
| [PROTOTYPE-BRIEF.md](../PROTOTYPE-BRIEF.md) | Ограниченная техническая постановка и правила выбора основы | Исходники среза P0/P1 подготовлены; запуск ERPNext и пригодность основы не подтверждены; [состояние](../prototype/README.md) |
| Уточнение пользователя 07.11.2026 о project timeline и Kanban-досках | Обязательные представления V1: U4, PLAN-01–PLAN-06, S21–S24 | Детальное поведение — предложение H; проверка PV1 не выполнена |
| Уточнение пользователя 11.11.2026 об окне затрат на такси и заправку служебных авто | Транспортные расходы в V1: U5, TRN-01–TRN-05, S25–S28, Q11 | Правила признания, распределения и доступа — предложение H; TV1 не выполнена |
