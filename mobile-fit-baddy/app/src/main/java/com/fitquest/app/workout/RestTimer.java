package com.fitquest.app.workout;

/**
 * Таймер отдыха. Чистый Java, без Android-классов: время приходит из Clock,
 * поэтому тестируется обычным unit-тестом. UI вызывает tick() раз в ~250 мс.
 */
public class RestTimer {

    public interface Clock { long nowMillis(); }
    public interface Listener { void onFinished(); } // один раз, не при skip

    public enum State { IDLE, RUNNING, PAUSED, FINISHED }

    public static final int[] PRESETS_SECONDS = {30, 60, 90, 120};
    public static final int EXTRA_SECONDS = 30;

    private final Clock clock;
    private Listener listener;
    private State state = State.IDLE;
    private long endAtMillis;
    private long pausedRemainingMillis;

    public RestTimer(Clock clock) { this.clock = clock; }

    public static RestTimer system() {
        return new RestTimer(() -> System.nanoTime() / 1_000_000L); // монотонные часы
    }

    public void setListener(Listener l) { this.listener = l; }

    public void start(int seconds) {
        if (seconds <= 0) throw new IllegalArgumentException("seconds must be > 0");
        endAtMillis = clock.nowMillis() + seconds * 1000L;
        state = State.RUNNING;
    }

    public void addSeconds(int seconds) {
        tick();
        if (state == State.RUNNING) endAtMillis += seconds * 1000L;
        else if (state == State.PAUSED) pausedRemainingMillis += seconds * 1000L;
    }

    public void pause() {
        tick();
        if (state == State.RUNNING) {
            pausedRemainingMillis = endAtMillis - clock.nowMillis();
            state = State.PAUSED;
        }
    }

    public void resume() {
        if (state == State.PAUSED) {
            endAtMillis = clock.nowMillis() + pausedRemainingMillis;
            state = State.RUNNING;
        }
    }

    public void skip() {
        if (state == State.RUNNING || state == State.PAUSED) state = State.IDLE;
    }

    public State tick() {
        if (state == State.RUNNING && clock.nowMillis() >= endAtMillis) {
            state = State.FINISHED;
            if (listener != null) listener.onFinished();
        }
        return state;
    }

    public State getState() { return state; }

    public long remainingMillis() {
        switch (state) {
            case RUNNING: return Math.max(0, endAtMillis - clock.nowMillis());
            case PAUSED:  return pausedRemainingMillis;
            default:      return 0;
        }
    }

    /** Округление вверх: при 0.2 с остатка на экране «1», а не «0». */
    public int remainingSeconds() { return (int) ((remainingMillis() + 999) / 1000); }
}