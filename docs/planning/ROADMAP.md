# Roadmap FitQuest

Проект: **11.09.2026 — 25.12.2026**, спринты по 2 недели (решение D-03). MVP — к **01.12.2026** (спринт 6). Сегодня — 14.10.2026, идёт **спринт 3**.

Задачи — `docs/planning/issues/subject-1/` (5 человек, по модулям) и `docs/planning/issues/subject-2/` (3 человека, по слоям). Один файл = один GitHub Issue; перенос — `scripts/create_issues.sh`. Доска: GitHub Projects — ссылка TODO после запуска скрипта (задача [PM-01](issues/subject-1/PM-01.md)).

## Спринты

| № | Даты | Тема | Цель спринта (пользовательский результат) |
|---|---|---|---|
| 1 | 11.09 – 24.09 | каркас, архитектура, первый сквозной путь | Через API (Swagger) пользователь регистрируется, создаёт программу и завершает тренировку — питомец получает XP, появляется уведомление. |
| 2 | 25.09 – 08.10 | экраны Android, телеметрия, ИИ на правилах, подписка | Все экраны MVP подключены к API: питомец, тренировки, прогресс, уведомления, живая телеметрия симулятора, mock-подписка. |
| 3 | 09.10 – 22.10 | качество, безопасность, документация, доска | Демо-путь защищён тестами и CI, известные дефекты безопасности закрыты, документы лаб 2–4 приведены в порядок. |
| 4 | 23.10 – 05.11 | правила питомца, повторы, Alembic, приём телеметрии | Питомец живёт по согласованным правилам (серия, сон, возвращение), расписание повторяется, backend готов принять данные от Raspberry Pi. |
| 5 | 06.11 – 19.11 | экран выполнения, квесты, календарь, тарифы | Пользователь проходит тренировку по подходам с таймером отдыха, видит расписание недели, квесты и календарь активности. |
| 6 | 20.11 – 03.12 | MVP, демо-прогон | MVP к 01.12.2026: полный демо-сценарий проходит на эмуляторе, напоминания и графики работают. |
| 7 | 04.12 – 17.12 | Pi end-to-end, доработки | Узел Raspberry Pi отдаёт шаги и пульс в приложение через backend; доработки по замечаниям. |
| 8 | 18.12 – 25.12 | сдача | Проект сдан: документация и матрица требований актуальны, демонстрация отрепетирована. |

**Спринт закрыт, когда:** все задачи спринта в колонке «Готово» или осознанно перенесены с комментарием; CI на `main` зелёный; цель спринта показана на эмуляторе или в Swagger; `REQUIREMENTS_TRACE.md` обновлён по закрытым критериям.

## Оценка: story points

- Шкала: **1, 2, 3, 5, 8, 13**. Задача крупнее 8 — дробится.
- Опорная задача — [ACC-02 «Вход и выдача JWT»](issues/subject-1/ACC-02.md) = **2 SP**: один endpoint, схема, тест, известная технология.
- Оценки — относительно опорной задачи (планирование покером на встрече спринта).
- Скорость команды предмета 1 по факту: спринт 1 — 60 SP, спринт 2 — 24 SP. Плановый объём следующих спринтов держим не выше этой скорости.

## Предмет 1 — по бизнес-модулям

Сделано **109** из **252** SP.

### Нагрузка: задачи / SP по спринтам

| Участник | С1 | С2 | С3 | С4 | С5 | С6 | С7 | С8 | Всего задач / SP | Сделано / осталось SP |
|---|---|---|---|---|---|---|---|---|---|---|
| @NastyaZhilinaRis2 | 5 / 12 | 1 / 3 | 3 / 7 | 2 / 6 | 3 / 11 | 2 / 3 | — | — | 16 / 42 | 22 / 20 |
| @Hupubu | 5 / 13 | 1 / 5 | 2 / 5 | 4 / 10 | 3 / 13 | — | — | — | 15 / 46 | 20 / 26 |
| @SonyAkb | 5 / 10 | 1 / 5 | 3 / 6 | 2 / 5 | 2 / 8 | 3 / 7 | — | 1 / 2 | 17 / 43 | 17 / 26 |
| @Ananasic07 | 3 / 8 | 1 / 3 | 3 / 7 | 1 / 3 | 3 / 9 | 3 / 8 | — | — | 14 / 38 | 18 / 20 |
| @MouseViolin | 5 / 17 | 3 / 8 | 3 / 7 | 3 / 8 | 6 / 16 | 5 / 19 | 3 / 8 | — | 28 / 83 | 32 / 51 |
| **Спринт, SP** | 60 | 24 | 32 | 32 | 57 | 37 | 8 | 2 | 90 / 252 | |

> @MouseViolin нагружен заметно сильнее остальных: в предмете 1 у него три подмодуля (ИИ, устройства, подписка) и узел Pi — так распределил владелец проекта. Экран тарифов отдан владелице вкладки Pack (@NastyaZhilinaRis2). Задачи Pi стоят в спринтах 5–7, после ядра MVP; при нехватке времени они первые кандидаты на перенос — работа на реальных датчиках в MoSCoW для MVP — Won't (W1).

### Бэклог по приоритету (истории → задачи)

| # | История | MoSCoW | Готово задач | Задачи |
|---|---|---|---|---|
| 1 | US-A1 | Must | 7 / 10 | [CORE-03](issues/subject-1/CORE-03.md) ✅, [DOC-04](issues/subject-1/DOC-04.md), [ACC-01](issues/subject-1/ACC-01.md) ✅, [ACC-02](issues/subject-1/ACC-02.md) ✅, [ACC-04](issues/subject-1/ACC-04.md) ✅, [ACC-06](issues/subject-1/ACC-06.md), [ACC-07](issues/subject-1/ACC-07.md), [AND-06](issues/subject-1/AND-06.md) ✅, [AND-01](issues/subject-1/AND-01.md) ✅, [AND-07](issues/subject-1/AND-07.md) ✅ |
| 2 | US-B1 | Must | 3 / 5 | [WKT-01](issues/subject-1/WKT-01.md) ✅, [WKT-02](issues/subject-1/WKT-02.md) ✅, [WKT-06](issues/subject-1/WKT-06.md), [WKT-07](issues/subject-1/WKT-07.md), [AND-03](issues/subject-1/AND-03.md) ✅ |
| 3 | US-C2 | Must | 3 / 7 | [DOC-04](issues/subject-1/DOC-04.md), [REL-01](issues/subject-1/REL-01.md), [WKT-01](issues/subject-1/WKT-01.md) ✅, [WKT-03](issues/subject-1/WKT-03.md) ✅, [WKT-08](issues/subject-1/WKT-08.md), [AND-03](issues/subject-1/AND-03.md) ✅, [AND-11](issues/subject-1/AND-11.md) |
| 4 | US-D1 | Must | 6 / 12 | [CORE-02](issues/subject-1/CORE-02.md) ✅, [DOC-04](issues/subject-1/DOC-04.md), [REL-01](issues/subject-1/REL-01.md), [WKT-09](issues/subject-1/WKT-09.md), [PET-01](issues/subject-1/PET-01.md) ✅, [PET-02](issues/subject-1/PET-02.md) ✅, [PET-03](issues/subject-1/PET-03.md) ✅, [PET-04](issues/subject-1/PET-04.md) ✅, [PET-05](issues/subject-1/PET-05.md), [PET-09](issues/subject-1/PET-09.md), [AND-02](issues/subject-1/AND-02.md) ✅, [AND-14](issues/subject-1/AND-14.md) |
| 5 | US-E1 | Must | 2 / 6 | [REL-01](issues/subject-1/REL-01.md), [WKT-08](issues/subject-1/WKT-08.md), [DSH-01](issues/subject-1/DSH-01.md) ✅, [DSH-02](issues/subject-1/DSH-02.md), [AND-04](issues/subject-1/AND-04.md) ✅, [AND-16](issues/subject-1/AND-16.md) |
| 6 | US-H1 | Must (симулятор) | 6 / 20 | [DEV-01](issues/subject-1/DEV-01.md) ✅, [DEV-02](issues/subject-1/DEV-02.md) ✅, [DEV-03](issues/subject-1/DEV-03.md) ✅, [DEV-04](issues/subject-1/DEV-04.md) ✅, [DEV-05](issues/subject-1/DEV-05.md), [DEV-06](issues/subject-1/DEV-06.md), [AND-05](issues/subject-1/AND-05.md) ✅, [AND-07](issues/subject-1/AND-07.md) ✅, [AND-08](issues/subject-1/AND-08.md), [AND-09](issues/subject-1/AND-09.md), [PI-01](issues/subject-1/PI-01.md), [PI-02](issues/subject-1/PI-02.md), [PI-03](issues/subject-1/PI-03.md), [PI-04](issues/subject-1/PI-04.md), [PI-05](issues/subject-1/PI-05.md), [PI-06](issues/subject-1/PI-06.md), [PI-07](issues/subject-1/PI-07.md), [PI-08](issues/subject-1/PI-08.md), [PI-09](issues/subject-1/PI-09.md), [PI-10](issues/subject-1/PI-10.md) |
| 7 | US-A2 | Must | 2 / 3 | [ACC-03](issues/subject-1/ACC-03.md) ✅, [ACC-05](issues/subject-1/ACC-05.md), [AND-06](issues/subject-1/AND-06.md) ✅ |
| 8 | US-B2 | Must | 2 / 4 | [SCH-01](issues/subject-1/SCH-01.md) ✅, [SCH-02](issues/subject-1/SCH-02.md) ✅, [SCH-03](issues/subject-1/SCH-03.md), [AND-18](issues/subject-1/AND-18.md) |
| 9 | US-C1 | Must | 0 / 3 | [WKT-08](issues/subject-1/WKT-08.md), [AND-11](issues/subject-1/AND-11.md), [AND-12](issues/subject-1/AND-12.md) |
| 10 | US-F2 | Must (уведомления о событиях) | 4 / 5 | [NTF-01](issues/subject-1/NTF-01.md) ✅, [NTF-02](issues/subject-1/NTF-02.md) ✅, [NTF-03](issues/subject-1/NTF-03.md) ✅, [NTF-04](issues/subject-1/NTF-04.md), [AND-04](issues/subject-1/AND-04.md) ✅ |
| 11 | US-C3 | Should | 3 / 3 | [WKT-04](issues/subject-1/WKT-04.md) ✅, [WKT-05](issues/subject-1/WKT-05.md) ✅, [AND-03](issues/subject-1/AND-03.md) ✅ |
| 12 | US-D2 | Should | 3 / 6 | [SCH-01](issues/subject-1/SCH-01.md) ✅, [PET-02](issues/subject-1/PET-02.md) ✅, [PET-04](issues/subject-1/PET-04.md) ✅, [PET-06](issues/subject-1/PET-06.md), [AND-14](issues/subject-1/AND-14.md), [NTF-04](issues/subject-1/NTF-04.md) |
| 13 | US-G1 | Should | 1 / 3 | [SUB-01](issues/subject-1/SUB-01.md) ✅, [SUB-03](issues/subject-1/SUB-03.md), [SUB-04](issues/subject-1/SUB-04.md) |
| 14 | US-G2 | Should | 2 / 3 | [SUB-01](issues/subject-1/SUB-01.md) ✅, [SUB-02](issues/subject-1/SUB-02.md) ✅, [SUB-04](issues/subject-1/SUB-04.md) |
| 15 | US-H2 | Should | 2 / 4 | [AI-01](issues/subject-1/AI-01.md) ✅, [AI-02](issues/subject-1/AI-02.md), [AI-03](issues/subject-1/AI-03.md), [SUB-02](issues/subject-1/SUB-02.md) ✅ |
| 16 | US-D3 | Should | 0 / 3 | [PET-07](issues/subject-1/PET-07.md), [PET-08](issues/subject-1/PET-08.md), [AND-13](issues/subject-1/AND-13.md) |
| 17 | US-E2 | Should | 0 / 2 | [DSH-03](issues/subject-1/DSH-03.md), [AND-15](issues/subject-1/AND-15.md) |
| 18 | US-B3 | Could | 0 / 2 | [SCH-04](issues/subject-1/SCH-04.md), [AND-18](issues/subject-1/AND-18.md) |
| 19 | US-F1 | Should | 0 / 1 | [AND-17](issues/subject-1/AND-17.md) |
| 20 | Технические и документационные | — | 6 / 10 | [CORE-01](issues/subject-1/CORE-01.md), [CORE-04](issues/subject-1/CORE-04.md), [CORE-05](issues/subject-1/CORE-05.md), [CORE-06](issues/subject-1/CORE-06.md), [DOC-01](issues/subject-1/DOC-01.md), [DOC-02](issues/subject-1/DOC-02.md), [DOC-03](issues/subject-1/DOC-03.md), [DOC-05](issues/subject-1/DOC-05.md), [PM-01](issues/subject-1/PM-01.md), [REL-02](issues/subject-1/REL-02.md) |

### Задачи по спринтам

#### Спринт 1 · 11.09 – 24.09 · 60 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [CORE-01](issues/subject-1/CORE-01.md) | [Core] Каркас FastAPI: конфиг, подключение PostgreSQL, Docker Compose | @MouseViolin | 3 | ✅ |
| [CORE-02](issues/subject-1/CORE-02.md) | [Core] Шина событий внутри процесса | @SonyAkb | 2 | ✅ |
| [CORE-03](issues/subject-1/CORE-03.md) | [Core] JWT и хеширование паролей | @NastyaZhilinaRis2 | 2 | ✅ |
| [DOC-01](issues/subject-1/DOC-01.md) | [Docs] Паспорт проекта в README и состав команды (лаба 1) | @SonyAkb | 2 | ✅ |
| [DOC-03](issues/subject-1/DOC-03.md) | [Docs] Пользовательские истории, критерии приёмки и MoSCoW | @Hupubu | 3 | ✅ |
| [ACC-01](issues/subject-1/ACC-01.md) | [Аккаунт] Модели User и Profile, регистрация | @NastyaZhilinaRis2 | 3 | ✅ |
| [ACC-02](issues/subject-1/ACC-02.md) | [Аккаунт] Вход и выдача JWT | @NastyaZhilinaRis2 | 2 | ✅ |
| [ACC-03](issues/subject-1/ACC-03.md) | [Аккаунт] Обновление профиля: цель, вес, уровень | @NastyaZhilinaRis2 | 2 | ✅ |
| [SCH-01](issues/subject-1/SCH-01.md) | [Расписание] CRUD слотов и отметка пропуска → WorkoutMissed | @NastyaZhilinaRis2 | 3 | ✅ |
| [WKT-01](issues/subject-1/WKT-01.md) | [Тренировки] Модели планов, упражнений плана и сессий | @Hupubu | 3 | ✅ |
| [WKT-02](issues/subject-1/WKT-02.md) | [Тренировки] API программ тренировок | @Hupubu | 2 | ✅ |
| [WKT-03](issues/subject-1/WKT-03.md) | [Тренировки] Старт и завершение сессии → WorkoutCompleted | @Hupubu | 3 | ✅ |
| [WKT-04](issues/subject-1/WKT-04.md) | [Тренировки] История тренировок | @Hupubu | 2 | ✅ |
| [PET-01](issues/subject-1/PET-01.md) | [Питомец] Модель питомца и создание при регистрации | @SonyAkb | 2 | ✅ |
| [PET-02](issues/subject-1/PET-02.md) | [Питомец] XP, уровень, настроение и серия по событиям | @SonyAkb | 3 | ✅ |
| [PET-03](issues/subject-1/PET-03.md) | [Питомец] GET /pet | @SonyAkb | 1 | ✅ |
| [NTF-01](issues/subject-1/NTF-01.md) | [Уведомления] Модель уведомлений и обработчики событий | @Ananasic07 | 3 | ✅ |
| [NTF-02](issues/subject-1/NTF-02.md) | [Уведомления] API списка и отметки прочтения | @Ananasic07 | 2 | ✅ |
| [DSH-01](issues/subject-1/DSH-01.md) | [Дашборд] Недельная сводка | @Ananasic07 | 3 | ✅ |
| [DEV-01](issues/subject-1/DEV-01.md) | [Устройства] Регистрация устройства и модель телеметрии | @MouseViolin | 3 | ✅ |
| [DEV-02](issues/subject-1/DEV-02.md) | [Устройства] Симулятор телеметрии: simulate, latest, history | @MouseViolin | 3 | ✅ |
| [DEV-03](issues/subject-1/DEV-03.md) | [Устройства] WebSocket живой телеметрии | @MouseViolin | 3 | ✅ |
| [AND-01](issues/subject-1/AND-01.md) | [Android] Каркас приложения: Retrofit, сессия, навигация | @MouseViolin | 5 | ✅ |

#### Спринт 2 · 25.09 – 08.10 · 24 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [AND-06](issues/subject-1/AND-06.md) | [Аккаунт] Android: Splash, вход/регистрация, профиль и выход | @NastyaZhilinaRis2 | 3 | ✅ |
| [AND-03](issues/subject-1/AND-03.md) | [Тренировки] Android: экран Quest — программы, сессия, история | @Hupubu | 5 | ✅ |
| [AND-02](issues/subject-1/AND-02.md) | [Питомец] Android: главный экран Den с питомцем | @SonyAkb | 5 | ✅ |
| [AND-04](issues/subject-1/AND-04.md) | [Дашборд] Android: экраны Trail (прогресс) и Calls (уведомления) | @Ananasic07 | 3 | ✅ |
| [AI-01](issues/subject-1/AI-01.md) | [ИИ] Рекомендация на правилах и история | @MouseViolin | 2 | ✅ |
| [SUB-01](issues/subject-1/SUB-01.md) | [Подписка] Тариф Free/Pro, mock checkout и идемпотентный webhook | @MouseViolin | 3 | ✅ |
| [AND-05](issues/subject-1/AND-05.md) | [Устройства] Android: экран Live watch — WS и запасной REST | @MouseViolin | 3 | ✅ |

#### Спринт 3 · 09.10 – 22.10 · 32 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [CORE-05](issues/subject-1/CORE-05.md) | [CI] GitHub Actions: отдельный job на backend, Android и Pi | @Ananasic07 | 3 | ✅ |
| [CORE-06](issues/subject-1/CORE-06.md) | [Docs] Стратегия тестирования и ручные сценарии | @Ananasic07 | 2 | ✅ |
| [DOC-02](issues/subject-1/DOC-02.md) | [Docs] Дополнительные роли участников в таблице команды | @SonyAkb | 1 | ⬜ |
| [DOC-04](issues/subject-1/DOC-04.md) | [Docs] Требования FR/NFR, три ключевые истории и границы MVP (лаба 2) | @Hupubu | 3 | 🟡 |
| [DOC-05](issues/subject-1/DOC-05.md) | [Docs] Архитектура проекта и UML-схема компонентов (лаба 3) | @NastyaZhilinaRis2 | 3 | ✅ |
| [PM-01](issues/subject-1/PM-01.md) | [PM] Бэклог, цель спринта, story points и доска GitHub Projects (лаба 4) | @SonyAkb | 3 | 🟡 |
| [ACC-04](issues/subject-1/ACC-04.md) | [Аккаунт] Refresh-токен и проверка типа токена | @NastyaZhilinaRis2 | 2 | ✅ |
| [SCH-02](issues/subject-1/SCH-02.md) | [Расписание] Запрет слотов в прошлом и фильтр по датам | @NastyaZhilinaRis2 | 2 | ✅ |
| [WKT-05](issues/subject-1/WKT-05.md) | [Тренировки] Пагинация истории и тесты модуля | @Hupubu | 2 | ✅ |
| [PET-04](issues/subject-1/PET-04.md) | [Питомец] Тесты правил питомца | @SonyAkb | 2 | ✅ |
| [NTF-03](issues/subject-1/NTF-03.md) | [Уведомления] Фильтр непрочитанных, лимит и тесты | @Ananasic07 | 2 | ✅ |
| [DEV-04](issues/subject-1/DEV-04.md) | [Устройства] Валидация телеметрии, фильтр периода, защита device_id | @MouseViolin | 2 | ✅ |
| [SUB-02](issues/subject-1/SUB-02.md) | [Подписка] Подпись webhook, PaymentProvider и проверка доступа can_use | @MouseViolin | 3 | ✅ |
| [AND-07](issues/subject-1/AND-07.md) | [Android] Unit-тесты: валидация форм, DTO, настроение | @MouseViolin | 2 | ✅ |

#### Спринт 4 · 23.10 – 05.11 · 32 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [CORE-04](issues/subject-1/CORE-04.md) | [Core] Подключить Alembic и первую миграцию | @Hupubu | 3 | ⬜ |
| [ACC-05](issues/subject-1/ACC-05.md) | [Аккаунт] Цель и уровень — фиксированные значения, онбординг профиля | @NastyaZhilinaRis2 | 3 | ⬜ |
| [SCH-03](issues/subject-1/SCH-03.md) | [Расписание] Повторяющиеся тренировки по дням недели | @NastyaZhilinaRis2 | 3 | ⬜ |
| [WKT-06](issues/subject-1/WKT-06.md) | [Тренировки] Каталог упражнений с поиском и группами мышц | @Hupubu | 3 | ⬜ |
| [WKT-07](issues/subject-1/WKT-07.md) | [Тренировки] Редактирование и удаление программ | @Hupubu | 2 | ⬜ |
| [WKT-09](issues/subject-1/WKT-09.md) | [Тренировки] Убрать начисление XP из модуля тренировок | @Hupubu | 2 | ⬜ |
| [PET-05](issues/subject-1/PET-05.md) | [Питомец] Правила XP: бонус серии, порог level×100, максимум 50 | @SonyAkb | 2 | ⬜ |
| [PET-06](issues/subject-1/PET-06.md) | [Питомец] Настроение по дням без тренировки, сон и бонус возвращения | @SonyAkb | 3 | ⬜ |
| [DSH-02](issues/subject-1/DSH-02.md) | [Дашборд] Период неделя/месяц, шаги за 7 дней, тренировки по дням | @Ananasic07 | 3 | ⬜ |
| [DEV-05](issues/subject-1/DEV-05.md) | [Устройства] Приём телеметрии от Raspberry Pi: POST /telemetry/ingest | @MouseViolin | 3 | ⬜ |
| [DEV-06](issues/subject-1/DEV-06.md) | [Устройства] WebSocket рассылает сохранённые точки, а не генерирует | @MouseViolin | 3 | ⬜ |
| [AND-08](issues/subject-1/AND-08.md) | [Устройства] Android: офлайн-кэш последней точки и статус с датой | @MouseViolin | 2 | ⬜ |

#### Спринт 5 · 06.11 – 19.11 · 57 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [SCH-04](issues/subject-1/SCH-04.md) | [Расписание] Перенос тренировки с проверкой конфликта | @NastyaZhilinaRis2 | 3 | ⬜ |
| [AND-18](issues/subject-1/AND-18.md) | [Расписание] Android: экран расписания на неделю | @NastyaZhilinaRis2 | 5 | ⬜ |
| [WKT-08](issues/subject-1/WKT-08.md) | [Тренировки] Фактические подходы: session exercises и sets | @Hupubu | 5 | ⬜ |
| [AND-11](issues/subject-1/AND-11.md) | [Тренировки] Android: экран выполнения с чек-листом подходов | @Hupubu | 5 | ⬜ |
| [AND-12](issues/subject-1/AND-12.md) | [Тренировки] Android: таймер отдыха | @Hupubu | 3 | ⬜ |
| [PET-07](issues/subject-1/PET-07.md) | [Питомец] Модели квестов и достижений с начальным набором | @SonyAkb | 3 | ⬜ |
| [PET-08](issues/subject-1/PET-08.md) | [Питомец] Прогресс квестов и выдача достижений по событиям | @SonyAkb | 5 | ⬜ |
| [NTF-04](issues/subject-1/NTF-04.md) | [Уведомления] Сообщения питомца на 2/5/7/14 день и база фраз | @Ananasic07 | 3 | ⬜ |
| [DSH-03](issues/subject-1/DSH-03.md) | [Дашборд] API календаря активности | @Ananasic07 | 3 | ⬜ |
| [AND-15](issues/subject-1/AND-15.md) | [Дашборд] Android: календарь активности | @Ananasic07 | 3 | ⬜ |
| [AI-02](issues/subject-1/AI-02.md) | [ИИ] Обоснование и интенсивность по истории тренировок | @MouseViolin | 3 | ⬜ |
| [SUB-03](issues/subject-1/SUB-03.md) | [Подписка] Лимит Free: не больше 2 программ | @MouseViolin | 2 | ⬜ |
| [SUB-04](issues/subject-1/SUB-04.md) | [Подписка] Android: экран тарифов Free/Pro во вкладке Pack | @NastyaZhilinaRis2 | 3 | ⬜ |
| [AND-09](issues/subject-1/AND-09.md) | [Устройства] Android: подключение узла Raspberry Pi и индикация источника | @MouseViolin | 2 | ⬜ |
| [PI-01](issues/subject-1/PI-01.md) | [Pi] Каркас узла: конфиг, часы, фабрика шины и FakeSMBus | @MouseViolin | 3 | ⬜ |
| [PI-02](issues/subject-1/PI-02.md) | [Pi] Виртуальный MPU6050: регистры, сон, диапазон | @MouseViolin | 3 | ⬜ |
| [PI-04](issues/subject-1/PI-04.md) | [Pi] Генераторы сигналов, сценарии и проигрыватель CSV | @MouseViolin | 3 | ⬜ |

#### Спринт 6 · 20.11 – 03.12 · 37 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [REL-01](issues/subject-1/REL-01.md) | [QA] Генеральный прогон демо-сценария MVP | @Ananasic07 | 2 | ⬜ |
| [ACC-06](issues/subject-1/ACC-06.md) | [Аккаунт] Ссылка «Забыли пароль?» — заглушка | @NastyaZhilinaRis2 | 1 | ⬜ |
| [ACC-07](issues/subject-1/ACC-07.md) | [Аккаунт] Android: обновление токена при 401 | @NastyaZhilinaRis2 | 2 | ⬜ |
| [PET-09](issues/subject-1/PET-09.md) | [Питомец] История событий питомца | @SonyAkb | 2 | ⬜ |
| [AND-13](issues/subject-1/AND-13.md) | [Питомец] Android: экран квестов и достижений | @SonyAkb | 3 | ⬜ |
| [AND-14](issues/subject-1/AND-14.md) | [Питомец] Android: анимации и реплики питомца по настроению | @SonyAkb | 2 | ⬜ |
| [AND-16](issues/subject-1/AND-16.md) | [Дашборд] Android: графики на экране прогресса | @Ananasic07 | 3 | ⬜ |
| [AND-17](issues/subject-1/AND-17.md) | [Уведомления] Android: локальные напоминания о тренировке | @Ananasic07 | 3 | ⬜ |
| [AI-03](issues/subject-1/AI-03.md) | [ИИ] Модель из Google Colab за интерфейсом RecommendationService | @MouseViolin | 5 | ⬜ |
| [PI-03](issues/subject-1/PI-03.md) | [Pi] Виртуальный MAX30102: FIFO, указатели, переполнение | @MouseViolin | 5 | ⬜ |
| [PI-05](issues/subject-1/PI-05.md) | [Pi] Драйверы Mpu6050 и Max30102 + тест переносимости | @MouseViolin | 3 | ⬜ |
| [PI-06](issues/subject-1/PI-06.md) | [Pi] Подсчёт шагов на потоке отсчётов | @MouseViolin | 3 | ⬜ |
| [PI-07](issues/subject-1/PI-07.md) | [Pi] Оценка пульса с отказом при слабом сигнале | @MouseViolin | 3 | ⬜ |

#### Спринт 7 · 04.12 – 17.12 · 8 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [PI-08](issues/subject-1/PI-08.md) | [Pi] Sampler и локальный API /device/* | @MouseViolin | 3 | ⬜ |
| [PI-09](issues/subject-1/PI-09.md) | [Pi] Публикатор TelemetryDTO в backend | @MouseViolin | 3 | ⬜ |
| [PI-10](issues/subject-1/PI-10.md) | [Pi] README узла, запись CSV и проверка на реальной плате | @MouseViolin | 2 | ⬜ |

#### Спринт 8 · 18.12 – 25.12 · 2 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [REL-02](issues/subject-1/REL-02.md) | [Docs] Финальная сверка документации и требований перед сдачей | @SonyAkb | 2 | ⬜ |


## Предмет 2 — по слоям

Сделано **68** из **138** SP.

### Нагрузка: задачи / SP по спринтам

| Участник | С1 | С2 | С3 | С4 | С5 | С6 | С7 | С8 | Всего задач / SP | Сделано / осталось SP |
|---|---|---|---|---|---|---|---|---|---|---|
| @Hupubu | 8 / 29 | 1 / 3 | 2 / 8 | 3 / 9 | 1 / 3 | 2 / 5 | — | — | 17 / 57 | 40 / 17 |
| @MouseViolin | 1 / 5 | 6 / 21 | 1 / 2 | 1 / 2 | 3 / 8 | 3 / 10 | 1 / 2 | — | 16 / 50 | 28 / 22 |
| @Soloveve | — | — | — | 3 / 9 | 3 / 11 | 3 / 9 | 1 / 2 | — | 10 / 31 | 0 / 31 |
| **Спринт, SP** | 34 | 24 | 10 | 20 | 22 | 24 | 4 | 0 | 43 / 138 | |

> У @Soloveve нет закрытых задач: модуль Pi начинается в спринте 4. Объём модуля (~31 SP) сопоставим с оставшейся работой остальных участников.

### Бэклог по приоритету (истории → задачи)

| # | История | MoSCoW | Готово задач | Задачи |
|---|---|---|---|---|
| 1 | US-A1 | Must | 5 / 6 | [BE-03](issues/subject-2/BE-03.md) ✅, [BE-10](issues/subject-2/BE-10.md) ✅, [AND-01](issues/subject-2/AND-01.md) ✅, [AND-02](issues/subject-2/AND-02.md) ✅, [AND-07](issues/subject-2/AND-07.md) ✅, [AND-11](issues/subject-2/AND-11.md) |
| 2 | US-B1 | Must | 2 / 2 | [BE-05](issues/subject-2/BE-05.md) ✅, [AND-04](issues/subject-2/AND-04.md) ✅ |
| 3 | US-C2 | Must | 2 / 2 | [BE-05](issues/subject-2/BE-05.md) ✅, [AND-04](issues/subject-2/AND-04.md) ✅ |
| 4 | US-D1 | Must | 2 / 2 | [BE-06](issues/subject-2/BE-06.md) ✅, [AND-03](issues/subject-2/AND-03.md) ✅ |
| 5 | US-E1 | Must | 2 / 2 | [BE-07](issues/subject-2/BE-07.md) ✅, [AND-05](issues/subject-2/AND-05.md) ✅ |
| 6 | US-H1 | Must (симулятор) | 3 / 20 | [BE-08](issues/subject-2/BE-08.md) ✅, [BE-10](issues/subject-2/BE-10.md) ✅, [BE-13](issues/subject-2/BE-13.md), [BE-14](issues/subject-2/BE-14.md), [BE-15](issues/subject-2/BE-15.md), [BE-16](issues/subject-2/BE-16.md), [AND-06](issues/subject-2/AND-06.md) ✅, [AND-08](issues/subject-2/AND-08.md), [AND-09](issues/subject-2/AND-09.md), [AND-10](issues/subject-2/AND-10.md), [PI-01](issues/subject-2/PI-01.md), [PI-02](issues/subject-2/PI-02.md), [PI-03](issues/subject-2/PI-03.md), [PI-04](issues/subject-2/PI-04.md), [PI-05](issues/subject-2/PI-05.md), [PI-06](issues/subject-2/PI-06.md), [PI-07](issues/subject-2/PI-07.md), [PI-08](issues/subject-2/PI-08.md), [PI-09](issues/subject-2/PI-09.md), [PI-10](issues/subject-2/PI-10.md) |
| 7 | US-A2 | Must | 2 / 2 | [BE-03](issues/subject-2/BE-03.md) ✅, [AND-02](issues/subject-2/AND-02.md) ✅ |
| 8 | US-B2 | Must | 1 / 1 | [BE-04](issues/subject-2/BE-04.md) ✅ |
| 9 | US-C1 | Must | 0 / 0 | — |
| 10 | US-F2 | Must (уведомления о событиях) | 2 / 2 | [BE-07](issues/subject-2/BE-07.md) ✅, [AND-05](issues/subject-2/AND-05.md) ✅ |
| 11 | US-C3 | Should | 2 / 2 | [BE-05](issues/subject-2/BE-05.md) ✅, [AND-04](issues/subject-2/AND-04.md) ✅ |
| 12 | US-D2 | Should | 1 / 1 | [BE-06](issues/subject-2/BE-06.md) ✅ |
| 13 | US-G1 | Should | 0 / 0 | — |
| 14 | US-G2 | Should | 2 / 2 | [BE-09](issues/subject-2/BE-09.md) ✅, [BE-10](issues/subject-2/BE-10.md) ✅ |
| 15 | US-H2 | Should | 2 / 7 | [BE-09](issues/subject-2/BE-09.md) ✅, [BE-17](issues/subject-2/BE-17.md), [AI-01](issues/subject-2/AI-01.md) ✅, [AI-02](issues/subject-2/AI-02.md), [AI-03](issues/subject-2/AI-03.md), [AI-04](issues/subject-2/AI-04.md), [AI-05](issues/subject-2/AI-05.md) |
| 16 | US-D3 | Should | 0 / 0 | — |
| 17 | US-E2 | Should | 0 / 0 | — |
| 18 | US-B3 | Could | 0 / 0 | — |
| 19 | US-F1 | Should | 0 / 0 | — |
| 20 | Технические и документационные | — | 3 / 4 | [BE-01](issues/subject-2/BE-01.md), [BE-02](issues/subject-2/BE-02.md), [BE-11](issues/subject-2/BE-11.md), [BE-12](issues/subject-2/BE-12.md) |

### Задачи по спринтам

#### Спринт 1 · 11.09 – 24.09 · 34 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-01](issues/subject-2/BE-01.md) | [Backend] Каркас FastAPI, PostgreSQL и Docker Compose | @Hupubu | 3 | ✅ |
| [BE-02](issues/subject-2/BE-02.md) | [Backend] Шина событий внутри процесса | @Hupubu | 2 | ✅ |
| [BE-03](issues/subject-2/BE-03.md) | [Backend] Регистрация, вход, JWT и профиль | @Hupubu | 5 | ✅ |
| [BE-04](issues/subject-2/BE-04.md) | [Backend] Расписание и событие пропуска | @Hupubu | 3 | ✅ |
| [BE-05](issues/subject-2/BE-05.md) | [Backend] Программы, сессии тренировок и история | @Hupubu | 5 | ✅ |
| [BE-06](issues/subject-2/BE-06.md) | [Backend] Питомец: XP, уровень, настроение по событиям | @Hupubu | 3 | ✅ |
| [BE-07](issues/subject-2/BE-07.md) | [Backend] Уведомления и сводка дашборда | @Hupubu | 3 | ✅ |
| [BE-08](issues/subject-2/BE-08.md) | [Backend] Устройства, телеметрия, симулятор и WebSocket | @Hupubu | 5 | ✅ |
| [AND-01](issues/subject-2/AND-01.md) | [Android] Каркас приложения: Retrofit, сессия, навигация | @MouseViolin | 5 | ✅ |

#### Спринт 2 · 25.09 – 08.10 · 24 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-09](issues/subject-2/BE-09.md) | [Backend] ИИ-рекомендации на правилах и mock-подписка | @Hupubu | 3 | ✅ |
| [AND-02](issues/subject-2/AND-02.md) | [Android] Splash, вход, регистрация, профиль | @MouseViolin | 3 | ✅ |
| [AND-03](issues/subject-2/AND-03.md) | [Android] Главный экран Den с питомцем | @MouseViolin | 5 | ✅ |
| [AND-04](issues/subject-2/AND-04.md) | [Android] Экран Quest: программы, сессия, история | @MouseViolin | 5 | ✅ |
| [AND-05](issues/subject-2/AND-05.md) | [Android] Экраны Trail и Calls | @MouseViolin | 3 | ✅ |
| [AND-06](issues/subject-2/AND-06.md) | [Android] Live watch: WebSocket и запасной REST | @MouseViolin | 3 | ✅ |
| [AI-01](issues/subject-2/AI-01.md) | [ИИ] Рекомендация на правилах с дисклеймером | @MouseViolin | 2 | ✅ |

#### Спринт 3 · 09.10 – 22.10 · 10 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-10](issues/subject-2/BE-10.md) | [Backend] Исправления безопасности и валидации (Д-1…Д-8) | @Hupubu | 5 | ✅ |
| [BE-11](issues/subject-2/BE-11.md) | [Backend] Тесты на PostgreSQL и CI-job | @Hupubu | 3 | ✅ |
| [AND-07](issues/subject-2/AND-07.md) | [Android] Unit-тесты и CI-job | @MouseViolin | 2 | ✅ |

#### Спринт 4 · 23.10 – 05.11 · 20 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-12](issues/subject-2/BE-12.md) | [Backend] Alembic-миграции | @Hupubu | 3 | ⬜ |
| [BE-13](issues/subject-2/BE-13.md) | [Backend] Приём телеметрии от Pi: POST /telemetry/ingest с X-Device-Token | @Hupubu | 3 | ⬜ |
| [BE-14](issues/subject-2/BE-14.md) | [Backend] WebSocket рассылает сохранённые точки | @Hupubu | 3 | ⬜ |
| [AND-08](issues/subject-2/AND-08.md) | [Android] Офлайн-кэш последней точки и статус с датой | @MouseViolin | 2 | ⬜ |
| [PI-01](issues/subject-2/PI-01.md) | [Pi] Каркас узла: конфиг, часы, фабрика шины и FakeSMBus | @Soloveve | 3 | ⬜ |
| [PI-02](issues/subject-2/PI-02.md) | [Pi] Виртуальный MPU6050: регистры, сон, диапазон | @Soloveve | 3 | ⬜ |
| [PI-04](issues/subject-2/PI-04.md) | [Pi] Генераторы сигналов, сценарии и проигрыватель CSV | @Soloveve | 3 | ⬜ |

#### Спринт 5 · 06.11 – 19.11 · 22 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-15](issues/subject-2/BE-15.md) | [Backend] Агрегаты телеметрии для графиков: шаги по дням, средний пульс | @Hupubu | 3 | ⬜ |
| [AND-09](issues/subject-2/AND-09.md) | [Android] Подключение узла Pi и индикация источника данных | @MouseViolin | 2 | ⬜ |
| [AND-10](issues/subject-2/AND-10.md) | [Android] История телеметрии за период с графиком | @MouseViolin | 3 | ⬜ |
| [AI-02](issues/subject-2/AI-02.md) | [ИИ] Подготовка данных истории активности для модели | @MouseViolin | 3 | ⬜ |
| [PI-03](issues/subject-2/PI-03.md) | [Pi] Виртуальный MAX30102: FIFO, указатели, переполнение | @Soloveve | 5 | ⬜ |
| [PI-05](issues/subject-2/PI-05.md) | [Pi] Драйверы Mpu6050 и Max30102 + тест переносимости | @Soloveve | 3 | ⬜ |
| [PI-06](issues/subject-2/PI-06.md) | [Pi] Подсчёт шагов на потоке отсчётов | @Soloveve | 3 | ⬜ |

#### Спринт 6 · 20.11 – 03.12 · 24 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [BE-16](issues/subject-2/BE-16.md) | [Backend] Сквозной контракт-тест: публикатор Pi ↔ ingest | @Hupubu | 2 | ⬜ |
| [BE-17](issues/subject-2/BE-17.md) | [Backend] Эндпоинт инференса модели ИИ | @Hupubu | 3 | ⬜ |
| [AND-11](issues/subject-2/AND-11.md) | [Android] Обновление токена при 401 | @MouseViolin | 2 | ⬜ |
| [AI-03](issues/subject-2/AI-03.md) | [ИИ] Пайплайн обучения в Google Colab | @MouseViolin | 5 | ⬜ |
| [AI-04](issues/subject-2/AI-04.md) | [ИИ] Интеграция модели в backend и приложение | @MouseViolin | 3 | ⬜ |
| [PI-07](issues/subject-2/PI-07.md) | [Pi] Оценка пульса с отказом при слабом сигнале | @Soloveve | 3 | ⬜ |
| [PI-08](issues/subject-2/PI-08.md) | [Pi] Sampler и локальный API /device/* | @Soloveve | 3 | ⬜ |
| [PI-09](issues/subject-2/PI-09.md) | [Pi] Публикатор TelemetryDTO в backend | @Soloveve | 3 | ⬜ |

#### Спринт 7 · 04.12 – 17.12 · 4 SP

| ID | Задача | Исполнитель | SP | Статус |
|---|---|---|---|---|
| [AI-05](issues/subject-2/AI-05.md) | [ИИ] Оценка качества рекомендаций и проверка дисклеймера | @MouseViolin | 2 | ⬜ |
| [PI-10](issues/subject-2/PI-10.md) | [Pi] README узла, запись CSV и проверка на реальной плате | @Soloveve | 2 | ⬜ |


## Путь до закрытия целей

| Цель | Что осталось | Спринт |
|---|---|---|
| Демо-сценарий MVP (`CLAUDE.md`) | экран выполнения с подходами и таймером, правила питомца, честная сводка | 4–6 |
| Лаба 1 | дополнительные роли в таблице команды ([DOC-02](issues/subject-1/DOC-02.md)) | 3 |
| Лаба 2 | согласовать `REQUIREMENTS.md` ([DOC-04](issues/subject-1/DOC-04.md)) | 3 |
| Лаба 3 | готово; пояснить формат `.puml` при сдаче | 3 |
| Лаба 4 | доска, issues, оценки ([PM-01](issues/subject-1/PM-01.md)) | 3 |
| Предмет 2: Pi | модуль `pi-fit-baddy` по `docs/pi.md` (PI-01…PI-10) | 4–7 |
| Предмет 2: мост | ingest, WS-рассылка, агрегаты (BE-13…BE-16) | 4–6 |
| Предмет 2: ИИ | данные, Colab, интеграция (AI-02…AI-05) — после файла требований к ИИ | 5–7 |
| Разнос по репозиториям (предмет 2) | после стабилизации — `git filter-repo --subdirectory-filter` на каждую папку | 7 |
