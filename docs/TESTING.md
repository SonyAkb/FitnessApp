# Тестирование FitQuest

Каждая часть тестируется отдельно и без остальных: так работает и CI, и разработчик на своём ноутбуке. Ручные проверки — там, где нужен экран или реальное железо.

| Часть | Что проверяем | Инструмент | Команда | В CI |
|---|---|---|---|---|
| backend | бизнес-правила сервисов, API-контракт, события, безопасность | pytest + FastAPI `TestClient` | `cd backend-fit-baddy && pytest` | да: PostgreSQL 16 и SQLite |
| Android | логика без UI: валидация форм, разбор DTO, отображение настроения | JUnit 4 | `cd mobile-fit-baddy && ./gradlew testDebugUnitTest` | да + `lintDebug`, `assembleDebug` |
| Raspberry Pi | шина и виртуальные чипы, драйверы, шаги и пульс, API `/device/*`, переносимость | pytest, `SENSOR_MODE=mock` | `cd pi-fit-baddy && SENSOR_MODE=mock GPIOZERO_PIN_FACTORY=mock pytest` | да |
| Сквозной сценарий | вход → тренировка → питомец → дашборд → уведомление → телеметрия | pytest + ручной прогон на эмуляторе | `pytest tests/test_api.py::test_full_demo_path` | да (API-часть) |

## Backend (`backend-fit-baddy/tests`)

**Уровни.**

- *Unit* — функции сервисов на реальной сессии БД, без HTTP: правила питомца (`test_pet.py`), `can_use` и провайдер оплаты (`test_ai_subscription.py`), шина событий (`test_events.py`), контракт `TelemetryDTO` (`test_devices.py`).
- *API / интеграционные* — запросы через `TestClient` к приложению целиком, с настоящей БД и обработчиками событий: остальные тесты.
- *Сквозной* — `test_api.py::test_full_demo_path`.

**БД.** По умолчанию тесты идут на SQLite в памяти (быстро, без Docker). В CI тот же набор прогоняется и на PostgreSQL 16 — так ловятся различия диалектов (часовые пояса, типы). Локально на PostgreSQL:

```bash
docker run -d --rm --name fq-test-pg -e POSTGRES_USER=fitquest -e POSTGRES_PASSWORD=fitquest \
  -e POSTGRES_DB=fitquest_test -p 55432:5432 postgres:16-alpine
DATABASE_URL=postgresql+psycopg2://fitquest:fitquest@localhost:55432/fitquest_test pytest
docker stop fq-test-pg
```

Каждый тест получает чистую схему (`drop_all` + `create_all` в фикстуре `client`). Фикстура `db_session` даёт сессию для unit-тестов сервисов. Хелперы `register_user`, `create_plan`, `complete_workout`, `WEBHOOK_HEADERS` — в `tests/conftest.py`.

| Файл | Модуль / владелец | Что покрыто |
|---|---|---|
| `test_auth.py` | auth — @NastyaZhilinaRis2 | регистрация (дубликат, слабый пароль, email), вход, refresh, тип токена, просроченный токен, профиль и валидация веса |
| `test_schedule.py` | auth/schedule — @NastyaZhilinaRis2 | создание слота, запрет прошлого, фильтр `from/to`, изменение/удаление, пропуск и повторный пропуск, чужие слоты |
| `test_workouts.py` | workouts — @Hupubu | план без упражнений, обязательные поля, повторный старт, длительность, чужая сессия, пагинация истории |
| `test_pet_quests.py` | pet — @SonyAkb | каждый квест (daily, weekly, повторный complete в тот же день, сброс daily/weekly), каждое достижение (+ запрет дублей), награды XP, оба GET-эндпоинта и 401, уведомление о завершении квеста |
| `test_pet.py` | pet — @SonyAkb | правила XP по D-13: базовые 25 за тренировку, бонус серии +5×(streak−1), накопительный порог `level×100`, потолок `MAX_LEVEL=50`, `xp_to_next_level`, чистота публичной `xp_for_workout` (WKT-09), стрик/пропуск/энергия |
| `test_notifications.py` | notifications, dashboard — @Ananasic07 | уведомления по событиям, порядок, прочитанные, `unread_only`, `limit`, чужие уведомления, поля сводки |
| `test_devices.py` | devices — @MouseViolin | контракт `TelemetryDTO` (одинаковый для simulator и raspberry_pi), валидация, 404 без точек, повторная/чужая регистрация устройства, фильтр истории, WebSocket |
| `test_ai_subscription.py` | ai, subscription — @MouseViolin | Free по умолчанию, ИИ только на Pro, checkout, подпись webhook, идемпотентность, неуспешная оплата, `can_use` |
| `test_events.py` | ядро | доставка событий, подписки модулей |
| `test_api.py` | сквозные | основные сценарии MVP |

Линтер: `ruff check --select E,F,W --ignore E501 app tests` — в CI не блокирует сборку.

## Android (`mobile-fit-baddy/app/src/test`)

Unit-тесты без эмулятора проверяют код, в котором есть логика:

| Тест | Что проверяет |
|---|---|
| `auth/AuthValidatorTest` | правила форм входа и регистрации совпадают с backend (US-A1) |
| `api/DtoParsingTest` | ответы из `docs/API_CONTRACT.md` разбираются в DTO; телеметрия Pi и симулятора одинаковой формы; история — объект с `items` |
| `ui/UiFormatTest` | настроение питомца → картинка и подпись; неизвестное настроение → покой |

Экраны (Activity/Fragment) проверяются вручную по сценариям ниже. Инструментальные тесты (`androidTest`) в CI не запускаются — нужен эмулятор.

**План (задачи фазы 6):** вынести логику таймера отдыха и переключения WS → REST в отдельные классы и покрыть тестами, когда появится экран выполнения тренировки.

## Raspberry Pi (`pi-fit-baddy/device/tests`)

По требованиям `docs/pi.md` §8 — всё без платы и без `smbus2`/`RPi.GPIO`:

- драйвер MPU6050: `WHO_AM_I`; без пробуждения данных нет; смена диапазона меняет масштаб; неверный адрес → `OSError(121)`;
- драйвер MAX30102: инициализация регистров; разбор байтов FIFO; переполнение → `OVF_COUNTER`;
- шаги: сценарий «ходьба N шагов» → N ± допуск; покой → 0;
- пульс: сценарий 72 уд/мин → 72 ± 3; слабый сигнал → `null`;
- API `/device/*` в режиме mock отвечает по контракту;
- переносимость: драйверы работают с подменённой шиной того же интерфейса;
- публикатор: формирует `TelemetryDTO` с `source=raspberry_pi` и калориями по шагам; при недоступном backend — буферизует.

Время в тестах — управляемые часы (`Clock`), без `time.sleep`.

## Ручные проверки

Выполняются перед демонстрацией на эмуляторе Android (API 34) с backend из `docker compose up`.

| ID | Сценарий | Ожидаемый результат | Критерии |
|---|---|---|---|
| M-01 | Зарегистрироваться, закрыть и открыть приложение | Сразу главный экран без входа; после «Выйти» — экран входа | US-A1.3 |
| M-02 | Регистрация с паролем `abcdefgh` | Ошибка у поля пароля, запрос не уходит | US-A1.1 |
| M-03 | Quest → создать план → Start → подождать 30 с → Complete | Тост о завершении; Den: XP +25, лиса радуется; Trail: +1 тренировка; Calls: поздравление | US-C2, US-D1, AC9.1 |
| M-04 | Четыре тренировки в разные дни (или XP ≥ 100) | Уровень 2, картинка «level up», уведомление о новом уровне | US-D1.2 |
| M-05 | Live watch → «Simulate beat» | Пульс, шаги и калории обновились, источник `simulator` | US-H1, AC7.3 |
| M-06 | Live watch открыт, остановить backend (`docker compose stop backend`) | Статус «WS failed…», затем опрос REST; после запуска backend данные снова идут | AC12.1–12.3 |
| M-07 | Trail → «Рекомендация» на Free | Сообщение, что нужна подписка Pro | AC10.2 |
| M-08 | Pack → «Checkout» → Trail → «Рекомендация» | Тариф Pro; рекомендация с предупреждением «не медицинский совет» | US-G2, AC10.1, AC11.8 |
| M-09 | Swagger `/docs`: webhook без заголовка `X-Mock-Signature` | 403 | AC11.6 |
| M-10 | Pi на плате: `i2cdetect -y 1`, затем `SENSOR_MODE=real` | Адреса 0x68 и 0x57; `/device/status` → `connected: true`; пульс в пределах ±5 от эталонного пульсометра | `docs/pi.md` §9.2 |
| M-11 | Live watch → «Источник данных» → «Connect Raspberry Pi»; запустить узел с показанным кодом (`PAIRING_CODE=<код>`, `PUBLISH_ENABLED=true`, `BACKEND_URL` — адрес backend: для эмулятора `10.0.2.2`, для телефона IP компьютера в Wi-Fi) | В списке «Connected» появился узел; в Live watch идут точки, шаги растут, источник отмечен как «Raspberry Pi», а не «Симулятор» | US-H1, AND-09 |
| M-12 | После M-11 отвязать узел в приложении | Узел получает 401 и пишет об этом в лог; новые точки от Pi не приходят | AND-09, DEV-05 |

Результаты ручных проверок перед сдачей записываются в описание PR или в issue спринта.

## CI

`.github/workflows/ci.yml`, на каждый `push` и `pull_request`:

- job `changes` определяет, какие папки менялись (`dorny/paths-filter`);
- `backend` — Python 3.11, кэш pip, сервис PostgreSQL 16, `pytest` на PostgreSQL и SQLite, ruff без блокировки;
- `mobile` — JDK 17, кэш Gradle, `testDebugUnitTest`, `lintDebug`, `assembleDebug`, отчёты — артефактом;
- `pi` — Python 3.11, `SENSOR_MODE=mock`, `GPIOZERO_PIN_FACTORY=mock`, `pytest`; пока в папке нет `requirements.txt`, шаги пропускаются.

Каждый job использует `working-directory` своей папки и не зависит от соседних.

Проверено локально 14.10.2026: backend — 77 тестов на SQLite и PostgreSQL 16; Android — 14 unit-тестов, lint и сборка APK; синтаксис workflow — `actionlint`.
