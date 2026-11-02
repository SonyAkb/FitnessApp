package com.fitquest.app.health;

import com.fitquest.app.api.dto.TelemetryBatchRequest;

import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Turns Health Connect records into TelemetryDTO points (pure logic, unit-tested).
 *
 * One point per finished bucket that has pulse samples: steps are accumulated since local
 * midnight (as watches show them), heart_rate is the bucket average, timestamp is the bucket end.
 * A bucket without pulse is skipped — the backend contract requires heart_rate.
 */
public final class TelemetryBuckets {

    public static final long BUCKET_MILLIS = 5 * 60 * 1000L;
    static final int HEART_RATE_MIN = 30;
    static final int HEART_RATE_MAX = 230;

    private TelemetryBuckets() {
    }

    /** A StepsRecord: count of steps between start and end. */
    public static final class Steps {
        final long startMillis;
        final long endMillis;
        final long count;

        public Steps(long startMillis, long endMillis, long count) {
            this.startMillis = startMillis;
            this.endMillis = endMillis;
            this.count = count;
        }
    }

    /** One sample of a HeartRateRecord. */
    public static final class Pulse {
        final long timeMillis;
        final long bpm;

        public Pulse(long timeMillis, long bpm) {
            this.timeMillis = timeMillis;
            this.bpm = bpm;
        }
    }

    public static List<TelemetryBatchRequest.Point> build(
            List<Steps> steps, List<Pulse> pulses, long fromMillis, long nowMillis, ZoneId zone) {
        List<TelemetryBatchRequest.Point> points = new ArrayList<>();
        long first = (fromMillis / BUCKET_MILLIS) * BUCKET_MILLIS;
        for (long start = first; start + BUCKET_MILLIS <= nowMillis; start += BUCKET_MILLIS) {
            long end = start + BUCKET_MILLIS;
            long sum = 0;
            int count = 0;
            for (Pulse p : pulses) {
                if (p.timeMillis >= start && p.timeMillis < end
                        && p.bpm >= HEART_RATE_MIN && p.bpm <= HEART_RATE_MAX) {
                    sum += p.bpm;
                    count++;
                }
            }
            if (count == 0) {
                continue;
            }
            long dayStart = ZonedDateTime.ofInstant(Instant.ofEpochMilli(end - 1), zone)
                    .toLocalDate().atStartOfDay(zone).toInstant().toEpochMilli();
            long daySteps = 0;
            for (Steps s : steps) {
                if (s.endMillis > dayStart && s.endMillis <= end) {
                    daySteps += s.count;
                }
            }
            int heartRate = (int) Math.round((double) sum / count);
            points.add(new TelemetryBatchRequest.Point(
                    (int) Math.min(daySteps, Integer.MAX_VALUE), heartRate, 0,
                    DateTimeFormatter.ISO_INSTANT.format(Instant.ofEpochMilli(end))));
        }
        return points;
    }
}
