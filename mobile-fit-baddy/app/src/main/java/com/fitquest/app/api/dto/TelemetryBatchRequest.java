package com.fitquest.app.api.dto;

import java.util.List;

/** POST /telemetry/batch: points read from Health Connect. */
public class TelemetryBatchRequest {
    public final String source = "health_connect";
    public final List<Point> points;

    public TelemetryBatchRequest(List<Point> points) {
        this.points = points;
    }

    public static class Point {
        public final int steps;
        public final int heart_rate;
        public final int calories;
        public final String timestamp;

        public Point(int steps, int heartRate, int calories, String timestamp) {
            this.steps = steps;
            this.heart_rate = heartRate;
            this.calories = calories;
            this.timestamp = timestamp;
        }
    }
}
