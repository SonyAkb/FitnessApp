package com.fitquest.app.health;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import com.fitquest.app.api.dto.TelemetryBatchRequest;

import java.time.Instant;
import java.time.ZoneId;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;

/** Health Connect records → TelemetryDTO points for POST /telemetry/batch. */
public class TelemetryBucketsTest {

    private static final ZoneId UTC = ZoneId.of("UTC");
    private static final long MIN = 60_000L;
    private static final long T0 = Instant.parse("2026-10-25T10:00:00Z").toEpochMilli();

    @Test
    public void averagesPulseAndAccumulatesStepsPerBucket() {
        List<TelemetryBuckets.Steps> steps = Arrays.asList(
                new TelemetryBuckets.Steps(T0, T0 + 2 * MIN, 100),
                new TelemetryBuckets.Steps(T0 + 6 * MIN, T0 + 8 * MIN, 50));
        List<TelemetryBuckets.Pulse> pulses = Arrays.asList(
                new TelemetryBuckets.Pulse(T0 + MIN, 70),
                new TelemetryBuckets.Pulse(T0 + 3 * MIN, 81),
                new TelemetryBuckets.Pulse(T0 + 7 * MIN, 90));

        List<TelemetryBatchRequest.Point> points = TelemetryBuckets.build(steps, pulses, T0, T0 + 10 * MIN, UTC);

        assertEquals(2, points.size());
        assertEquals(76, points.get(0).heart_rate);              // (70 + 81) / 2 rounded
        assertEquals(100, points.get(0).steps);
        assertEquals("2026-10-25T10:05:00Z", points.get(0).timestamp);
        assertEquals(150, points.get(1).steps);                  // accumulated since midnight
        assertEquals(90, points.get(1).heart_rate);
    }

    @Test
    public void bucketWithoutPulseOrUnfinishedIsSkipped() {
        List<TelemetryBuckets.Pulse> pulses = Collections.singletonList(new TelemetryBuckets.Pulse(T0 + 11 * MIN, 80));
        List<TelemetryBatchRequest.Point> points = TelemetryBuckets.build(
                Collections.emptyList(), pulses, T0, T0 + 12 * MIN, UTC);
        assertTrue(points.isEmpty());
    }

    @Test
    public void implausiblePulseIsIgnored() {
        List<TelemetryBuckets.Pulse> pulses = Arrays.asList(
                new TelemetryBuckets.Pulse(T0 + MIN, 10), new TelemetryBuckets.Pulse(T0 + 2 * MIN, 250));
        assertTrue(TelemetryBuckets.build(Collections.emptyList(), pulses, T0, T0 + 5 * MIN, UTC).isEmpty());
    }

    @Test
    public void stepsResetAtLocalMidnight() {
        long beforeMidnight = Instant.parse("2026-10-24T23:50:00Z").toEpochMilli();
        long afterMidnight = Instant.parse("2026-10-25T00:00:00Z").toEpochMilli();
        List<TelemetryBuckets.Steps> steps = Arrays.asList(
                new TelemetryBuckets.Steps(beforeMidnight, beforeMidnight + MIN, 500),
                new TelemetryBuckets.Steps(afterMidnight, afterMidnight + MIN, 20));
        List<TelemetryBuckets.Pulse> pulses = Collections.singletonList(new TelemetryBuckets.Pulse(afterMidnight + 2 * MIN, 75));
        List<TelemetryBatchRequest.Point> points = TelemetryBuckets.build(steps, pulses, beforeMidnight, afterMidnight + 5 * MIN, UTC);
        assertEquals(1, points.size());
        assertEquals(20, points.get(0).steps);
    }
}
