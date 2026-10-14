# FitQuest Android (`mobile-fit-baddy`)

Нативное Android-приложение FitQuest на Java — основной клиент. Работает с backend по REST (`/api/v1`) и WebSocket (живые пульс и шаги). Источник телеметрии (симулятор или Raspberry Pi) приложению неважен: оно читает один и тот же `TelemetryDTO`.

> Папка самодостаточна: Gradle-проект с wrapper, собирается и тестируется без остальных частей репозитория. Для работы приложения нужен запущенный backend (`backend-fit-baddy`).

## Требования

- Android Studio Hedgehog или новее, Android SDK 34, JDK 17 (входит в Android Studio).
- Эмулятор или устройство с Android 8.0+ (API 26).

## Запуск

1. Android Studio → **File → Open** → эта папка.
2. Дождаться Gradle Sync. Файл `local.properties` с путём к SDK Studio создаёт сама (в git его нет).
3. Запустить конфигурацию `app`.

Командная строка:

```bash
./gradlew assembleDebug          # APK: app/build/outputs/apk/debug/
./gradlew installDebug           # установить на запущенный эмулятор
./gradlew testDebugUnitTest      # unit-тесты без эмулятора
./gradlew lintDebug              # Android Lint
```

## Адрес backend

По умолчанию — `http://10.0.2.2:8000` (так эмулятор видит `localhost` компьютера). Задаётся в `app/build.gradle.kts` (`BuildConfig.API_BASE_URL`) и меняется без пересборки: вкладка **Pack** → «API base URL» → «Save base URL».

| Где запущено | Base URL |
|---|---|
| Эмулятор Android | `http://10.0.2.2:8000` |
| Телефон в той же Wi-Fi | `http://<LAN-IP-компьютера>:8000` |
| Genymotion | `http://10.0.3.2:8000` |

Для локального демо разрешён cleartext HTTP (`usesCleartextTraffic`).

## Экраны

Нижняя навигация: **Den** (питомец, сегодняшняя тренировка) · **Quest** (программы, сессия, история) · **Trail** (прогресс, ИИ-рекомендация) · **Calls** (уведомления) · **Pack** (профиль, тариф, выход). Отдельный экран **Live watch** — пульс и шаги.

Какие методы API вызывает каждый экран — [SCREENS.md](SCREENS.md).

## Структура кода

```
app/src/main/java/com/fitquest/app/
  FitQuestApp.java         Application, доступ к SessionStore
  api/                     Retrofit-интерфейс FitQuestApi, ApiClient, AuthInterceptor, DTO
  auth/SessionStore.java   JWT и активная сессия (EncryptedSharedPreferences)
  ws/TelemetryWebSocket    WS-клиент телеметрии
  ui/                      Activity и Fragment по экранам (home, workout, progress, notifications, profile, telemetry)
app/src/main/res/          разметка, изображения питомца (кадры анимации — из Animation_1/)
```

## Поведение

- JWT хранится в EncryptedSharedPreferences; ответ `401` на любой запрос → выход на экран входа.
- Таймер тренировки локальный; на сервер уходит только `POST /workouts/sessions/{id}/complete` с длительностью.
- Телеметрия: WS `ws://…/api/v1/telemetry/ws` (первое сообщение `{"token":"<jwt>"}`); при обрыве — опрос `GET /api/v1/telemetry/latest` каждые 5 секунд и статус «офлайн».
- Игровые правила (XP, уровень, настроение) считает сервер — приложение только показывает состояние.

## Тесты

Unit-тесты бизнес-логики (без эмулятора) — `app/src/test/`, запуск `./gradlew testDebugUnitTest`. Что покрывается и что проверяется вручную — [`docs/TESTING.md`](../docs/TESTING.md).

## Владельцы

Предмет 2 — @MouseViolin (слой Android). Предмет 1 — экраны принадлежат владельцам модулей: Auth/Pack — @NastyaZhilinaRis2, Quest — @Hupubu, Den — @SonyAkb, Trail/Calls — @Ananasic07, Live watch и тариф — @MouseViolin.
