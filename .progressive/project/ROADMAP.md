# Roadmap — AV Integration Business Platform

Legend: `[ ] PLANNED` · `[>] IN PROGRESS` · `[x] COMPLETE`

Фазы соответствуют этапам [MVP-SPEC §15.1](../../MVP-SPEC.md#151-этапы-и-условия-перехода); условия перехода — там. Внедрение модулей и рабочих мест начинается только после TP Gate.

- [>] Phase 00 — Technical Proof (TP Gate) — `.progressive/phases/00-technical-proof.md`
- [ ] Phase 01 — Real-Project Validation (F1–F6, карточка scope) — `.progressive/phases/01-real-project-validation.md`
- [ ] Phase 02 — Limited Operational Pilot (PG-01–PG-08) — `.progressive/phases/02-limited-pilot.md`
- [ ] Phase 03 — Internal V1 (S01–S28, P0–P8, PV1, TV1) — `.progressive/phases/03-internal-v1.md`
- [ ] Phase 04 — Commercialization (вторая компания, распространение, лицензии) — `.progressive/phases/04-commercialization.md`

Подготовка Phase 01 (разбор документов реального проекта) может идти параллельно Phase 00 без загрузки данных в прототип.

Решение пользователя 12.11.2026: «Я б первую очередь офкусировался бы в интерфейсе продукта», затем выбор «Рабочее место Sales». Поэтому UI-01 (рабочее место Sales на Vue + frappe-ui поверх среза Sales → PM) идёт внутри Phase 00 до закрытия TP Gate. UI-01 не добавляет серверных правил: только показывает данные и вызывает существующие проверки Frappe. Остальные рабочие места — по-прежнему после TP Gate.

Решение пользователя 14.11.2026: «Я б сосредаточился бы сперва созданием mast-have функции. Такие как Kabnab доски, Whiteboard и другие», затем «Да, начинаем PM-01». Поэтому PM-01 (Kanban работ проекта, MVP-SPEC §11.1) идёт внутри Phase 00 раньше TP-02. Предложенный порядок H: PM-02 «Мои задачи» и список, PM-03 timeline, PM-04 доска Excalidraw. Каждый шаг начинается только по решению пользователя. Чат и автоматизации в V1 не входят (MVP-SPEC §2).

Project complete when all phase acceptance criteria are verified and every phase is `[x]`.
