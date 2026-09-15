# FitQuest Android (Java)

Native Android client for the FitQuest educational MVP. It talks to the FastAPI backend over REST (`/api/v1`) and optionally WebSocket for live telemetry.

This folder is a **Gradle Android app**. Open it in Android Studio — do not treat the React `frontend/` as the real client.

## Open in Android Studio

1. Start Android Studio (Hedgehog / Iguana / Koala or newer with Android SDK 34).
2. **File → Open** and select this directory:
   `FitnessApp/mobile-fit-baddy`
3. Wait for Gradle sync. JDK 17 is required (Android Studio usually bundles it).
4. Create an emulator with **API 26+** (Pixel 6 / API 34 is a good default).
5. Run the `app` configuration.

Command line (from this folder):

```bash
./gradlew :app:assembleDebug
# then install on a running emulator:
./gradlew :app:installDebug
```

`local.properties` must contain `sdk.dir=` pointing at your Android SDK. Android Studio writes this file automatically. It is gitignored.

## Backend (required)

The app expects the FitQuest API on port **8000**.

From the repo root:

```bash
docker compose up --build
```

If the team is using the parallel `backend-fit-baddy` service, start that instead — same contract, same port.

Swagger should answer at `http://localhost:8000/docs`.

## Base URL

Default (compiled into `BuildConfig.API_BASE_URL`):

```
http://10.0.2.2:8000
```

`10.0.2.2` is the Android emulator’s alias for the host machine’s localhost. Cleartext HTTP is enabled for local demo (`usesCleartextTraffic`).

| Where you run the app | Base URL |
| --- | --- |
| Android emulator | `http://10.0.2.2:8000` |
| Physical phone on the same Wi‑Fi | `http://<LAN-IP-of-your-computer>:8000` (example: `http://192.168.1.42:8000`) |
| Genymotion | often `http://10.0.3.2:8000` |

Change it without rebuilding:

1. Sign in
2. Open **Pack** (profile)
3. Edit **API base URL** → **Save base URL**
4. Leave the den and sign in again if requests still fail

You can also change the default in `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000\"")
```

## Screens

Bottom nav: **Den** (home) · **Quest** (workouts) · **Trail** (dashboard) · **Calls** (notifications) · **Pack** (profile).

Live telemetry is a full screen opened from Den or Pack.

See [SCREENS.md](SCREENS.md) for which API methods each screen calls.

## Demo path

1. Register / login
2. Den: fox XP / mood / streak, today’s quest teaser, last pulse & steps
3. Quest: craft a simple plan if the list is empty → **Start** → **Complete**
4. Back to Den / Trail: pet and stats should refresh
5. Live watch: **Simulate beat** if no device is sending data
6. Pack: save name/goal, mock checkout

## Notes

- No secrets are stored in the repo. JWT lives in EncryptedSharedPreferences (plaintext SharedPreferences fallback on broken Keystore).
- WebSocket: `ws://…/api/v1/telemetry/ws`, first message `{"token":"<jwt>"}`. If the socket fails, the screen polls `GET /api/v1/telemetry/latest` every 5 seconds.
- Do not copy this client against Raspberry Pi internals — the phone only sees the HTTP/WS contract.
