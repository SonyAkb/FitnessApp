package com.fitquest.app.workout;

import static org.junit.Assert.*;

import org.junit.Test;

public class RestTimerTest {

    private static class FakeClock implements RestTimer.Clock {
        long now = 1_000;
        public long nowMillis() { return now; }
        void advanceSeconds(int s) { now += s * 1000L; }
    }

    private final FakeClock clock = new FakeClock();
    private final RestTimer timer = new RestTimer(clock);

    @Test
    public void start_countsDown() {
        timer.start(60);
        assertEquals(RestTimer.State.RUNNING, timer.getState());
        assertEquals(60, timer.remainingSeconds());
        clock.advanceSeconds(10);
        assertEquals(50, timer.remainingSeconds());
    }

    @Test
    public void addSeconds_extendsRunningTimer() {
        timer.start(30);
        clock.advanceSeconds(10);
        timer.addSeconds(RestTimer.EXTRA_SECONDS);
        assertEquals(50, timer.remainingSeconds());
    }

    @Test
    public void pause_freezesTimeAndResumeContinues() {
        timer.start(60);
        clock.advanceSeconds(20);
        timer.pause();
        clock.advanceSeconds(100);               // на паузе время не идёт
        assertEquals(RestTimer.State.PAUSED, timer.getState());
        assertEquals(40, timer.remainingSeconds());
        timer.resume();
        clock.advanceSeconds(10);
        assertEquals(30, timer.remainingSeconds());
    }

    @Test
    public void addSeconds_worksOnPause() {
        timer.start(30);
        timer.pause();
        timer.addSeconds(30);
        assertEquals(60, timer.remainingSeconds());
    }

    @Test
    public void finish_firesListenerOnce() {
        final int[] calls = {0};
        timer.setListener(() -> calls[0]++);
        timer.start(30);
        clock.advanceSeconds(29);
        timer.tick();
        assertEquals(0, calls[0]);
        clock.advanceSeconds(1);
        assertEquals(RestTimer.State.FINISHED, timer.tick());
        timer.tick();
        assertEquals(1, calls[0]);
        assertEquals(0, timer.remainingSeconds());
    }

    @Test
    public void skip_resetsWithoutFinishing() {
        final int[] calls = {0};
        timer.setListener(() -> calls[0]++);
        timer.start(30);
        timer.skip();
        clock.advanceSeconds(60);
        timer.tick();
        assertEquals(RestTimer.State.IDLE, timer.getState());
        assertEquals(0, calls[0]);
    }

    @Test(expected = IllegalArgumentException.class)
    public void start_rejectsNonPositive() {
        timer.start(0);
    }
}