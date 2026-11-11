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

| C10 | [CxAlloy](https://cxalloy.com/), [Commissioning project management](https://www.cxalloy.com/commissioning-project-management/), [блог CxAlloy](https://blog.cxalloy.com/) | Чек-листы и тесты по оборудованию, шаблоны тестов, адресация дефектов, работа без связи, сканирование этикеток |
| C11 | [Fieldwire Help Center](https://help.fieldwire.com/hc/en-us/articles/202176374) | Версии листов, задачи на плане, списки замечаний, формы, работа без связи |
| C12 | [Fieldwire на G2](https://www.g2.com/products/fieldwire/features) | Агрегатор; использован только как указатель на функции, не как доказательство |
| C13 | [simPRO: Create a PO from within a job](https://helpguide.simprogroup.com/Content/Service-and-Enterprise/Create-a-PO-from-within-job.htm) | Заказ поставщику из работы и учёт обязательств; справка от 12.12.2025 |
| C14 | [simPRO Inventory](https://www.simprogroup.com/features/inventory-management-software) | Распределение запаса по работам, отчёт о требуемом запасе; маркетинговая страница, состав зависит от региона |
| C15 | [Procore: Budget Forecast Report](https://support.procore.com/faq/how-does-the-budget-forecast-report), [Forecast to Complete](https://v2.support.procore.com/en-au/product-manuals/budget-project/tutorials/use-the-forecast-to-complete-feature) | Раздельные обязательства, ожидаемые изменения и прогноз до завершения; связь с RFI не подтверждена |
| C16 | [Solar Power World о Scoop](https://www.solarpowerworldonline.com/2021/10/take-the-friction-out-of-solar-installations-and-om-service-to-speed-up-growth-and-boost-profits/), [разбор SunSystem Technology](https://www.casestudies.com/company/scoop-solar/case-study/sunsystem-technology-customer-case-study) | Настраиваемые процессы по фазам, мобильные формы, работа без связи; неофициальные материалы 2021 года и позже |
| C17 | [Q360 Features and Functions](https://solutions360.com/wp-content/uploads/2022/05/Q360-Features-and-Functions-2.pdf), [Solutions360](https://solutions360.com) | Сервисные контракты, отчёты по незавершённым работам, прибыльность проекта; документ 2022 года |
| C18 | [AVI Systems и Q360](https://www.securitysales.com/sponsored/avi-systems-solutions360-q360/159071/) | Заявление клиента о доходности сервисных направлений; спонсируемый материал |
| C19 | [RocketReach: Redmouse Audio Visual Integration](https://rocketreach.co/redmouse-audio-visual-integration-profile_b42e8cd2fecbff92) | Город и примерная численность образца целевого клиента; агрегатор контактов, пользователь подтвердил только то, что компания определена верно |

C10–C19 добавлены 11.11.2026 и получены через поисковую выдачу с краткими пересказами; страницы целиком не читались. Это отступление от правила в начале документа об исключении агрегаторов: C12, C16, C18 и C19 не являются официальной документацией и помечены соответственно. Выводы по ним — в [разделе 8 обзора референсов](02-reference-products.md#8-смежные-отрасли-что-перенять).

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
| Поручение пользователя 11.11.2026 обновить спеки по предоставленному аудиту | U6/E3; этапы, Pilot Gate, учёт доказательств и очередь проверки | Не подтверждает факты внешнего аудита и не разрешает автоматически выполнять вложенное ТЗ |
| Слова пользователя 11.11.2026 о цели «дать миру профессиональный продукт» для компаний вроде Red Mouse AV Integration и согласие с четырьмя решениями | U7; MVP-SPEC §1, §2.1 (ARC-01–ARC-04), этап 4 и Q10. Меняет прежнюю запись «только внутренний продукт» и статус DEFERRED для коммерческой цели в таблице раздела 10 | Сроки, модель распространения, цена и спрос не определены; граница V1 не расширена |
| Обзор смежных продуктов 11.11.2026 | E4; research/02 §8, MVP-SPEC §2.2, источники C10–C19 | Поисковая выдача, не чтение документации и не испытание; все переносы — предложения H |

## 10. Учёт предоставленного аудита 11 ноября 2026

Источник E3 — «Стратегический и технический аудит AV Integration Business Platform», предоставленный пользователем в файле [Untitled-1.md](<C:/Users/Khusan Turaev/Downloads/Telegram Desktop/Untitled-1.md>). Документ состоит из русской оценки и англоязычного задания будущему агенту; указан reference commit `670d853c7736`. Исходник оставлен по этому пути, не дублируется в спеках; локальная ссылка доступна только на машине владельца. Происхождение и принятые выводы сохранены здесь для читателей репозитория.

При переносе осмотрены README, MVP-SPEC, PROTOTYPE-BRIEF, исследование основы/пилота, план F1–F6, сохранённый отчёт прототипа и структура исходников; дополнительно прочитаны правила снимка в `commercial.py`. Рабочее дерево было чистым; текущий HEAD до правок — `ab13569f450e8772d8e2878555a64c5e43d9fb81`. После reference commit добавлен коммит документации `ab13569` с концептами ролевых рабочих мест. Это не новое доказательство runtime. Полный аудит реализации, тесты приложения, проверка Docker, лицензий и внешних источников при переносе не выполнялись. Факты о среде и 8/11 тестах относятся к отчёту 05.11.2026, а не новому запуску.

Канонические владельцы сохранены по карте README: **MVP-SPEC** — продукт, инварианты, источники фактов, критерии и открытые Q; **PROTOTYPE-BRIEF** — технические эксперименты, условия выбора основы и ближайшая очередь; **prototype/README** — записанные результаты исполнения; **06-real-project-validation** — метод и наблюдения F1–F6; этот реестр — происхождение и решения по входящим материалам. Новая параллельная система планирования не создаётся.

| Вывод E3 | Решение | Основание / канонический владелец |
|---|---|---|
| Разделить техническое доказательство, проверку проекта, пилот, V1 и коммерциализацию | ACCEPTED | MVP-SPEC §15.1; английский Stage 1 выделен отдельно, русская последовательность уточнена без удаления V1 |
| Ввести самостоятельный Pilot Gate | ACCEPTED | MVP-SPEC §15.2: PG-01–PG-08, scope и остановка; заменяет прежнюю неявную границу «применимые S» |
| Разделять описание, код, проверку и работу компании | ACCEPTED | MVP-SPEC §1.1; PROTOTYPE-BRIEF §4.2. Blocked учитывается отдельно от реализации, а результат запуска отдельно от зрелости |
| Сначала проверить имеющийся Sales → PM, включая конкурентность, права, rollback и restore | MERGED | Существующие P0/P1 и отчёт прототипа; PROTOTYPE-BRIEF §4.1/8 уточняют критерии и недостающие проверки, не заявляя результат |
| Устранить разрыв между целым основным Q2 и частичным выбором S01 | MERGED | SAL-06/S01 уже требуют частичный выбор; ограничение явно есть в prototype/README. MVP-SPEC §1.1/PG-04 и задача PG-READY сохраняют его открытым; решение реализации после scope |
| Один владелец каждого факта, без повторного ввода | MERGED | MVP-SPEC §5: таблица уже существует, добавлены обязательное заполнение до пилота и сравнение маршрутов ввода |
| Различать монтаж, конфигурацию, проверку и приёмку; версии и доказательства | ALREADY_COVERED | MVP-SPEC §7–12, S02/S05–S08; PG-07 связывает эти правила с допуском, новые дублирующие сущности не вводятся |
| Не удваивать затраты, EAC = AC + OC + ETC + R, выплаты отдельно, неизвестное не ноль | ALREADY_COVERED | MVP-SPEC §13–14, T1/K0–K3, TRN-04, P5/TV1; PG-06 требует фактическую сверку |
| Реальный проект, доступность поля и измерение пользы | MERGED | План F1–F6 и MVP-SPEC §15.3 уже содержат гипотезы; добавлены baseline, знаменатель полноты и явное отсутствие результатов |
| ERPNext — кандидат, проверять сопровождение/обновления и сравнивать альтернативы при ограничении | ALREADY_COVERED | Q9, PROTOTYPE-BRIEF §6, research/03 §2/4; условные исходы уточнены, стек не выбран заново |
| Объявить контрольную сумму гарантией защиты снимка | REJECTED | SHA-256 не подпись и не защита от совместного изменения данных/хеша; PROTOTYPE-BRIEF §4.1 фиксирует границу гарантии |
| Утвердить пороги 3 минуты / 30 секунд / 95% как доказанные нормы | REJECTED | MVP-SPEC §15.3: только предлагаемые гипотезы; до оценки нужны согласованный набор и baseline |
| Решить финансовую политику, полномочия, складские источники и необходимость offline | NEEDS_DECISION | Сохранены Q1–Q8/Q11 и F1–F6; нужны конкретные артефакты и ответственные компании. Документ не закрывает их предположением |
| Уточнить лицензию собственного приложения и будущую модель распространения | NEEDS_DECISION | Q10 и research/03 §4: декларация Proprietary не заменяет выбранной политики; нужен отдельный разбор состава и способа использования/распространения, юридический вывод не сделан |
| ИИ, автоматическое управление AV, SaaS и коммерческая экспансия | DEFERRED | Граница MVP-SPEC §2 и этап 4; сначала внутренний результат, затем доказанная потребность и отдельное решение |
| Выполнить вложенное ТЗ целиком: девять отчётов, полный аудит и backlog всех модулей | DEFERRED | Пользователь поручил обновить спеки. Перенос не является исполнением аудита; ближайшие проверочные задачи определены в PROTOTYPE-BRIEF §8 |

Статусы решений относятся к переносу материала, не к готовности продукта. Исторические результаты прототипа не переписаны, Q1–Q11 не закрыты, S01–S28/P0–P8/PV1/TV1 не объявлены пройденными. Следующая передача в исполнение — TP-01; функциональная реализация этим обновлением не выполняется.
