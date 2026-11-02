package com.fitquest.app.health;

import android.content.Context;
import android.content.pm.PackageManager;
import android.health.connect.HealthConnectException;
import android.health.connect.HealthConnectManager;
import android.health.connect.ReadRecordsRequestUsingFilters;
import android.health.connect.ReadRecordsResponse;
import android.health.connect.TimeInstantRangeFilter;
import android.health.connect.datatypes.HeartRateRecord;
import android.health.connect.datatypes.StepsRecord;
import android.os.Build;
import android.os.OutcomeReceiver;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.core.content.ContextCompat;

import com.fitquest.app.api.dto.TelemetryBatchRequest;

import java.time.Instant;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.function.Consumer;

/**
 * Reads steps and pulse that watches and bands (Mi Fitness, Zepp, Samsung Health, Fitbit…)
 * write to Health Connect. Uses the platform API of Android 14+, so no extra library is needed;
 * on older Android {@link #isSupported()} is false and the rest of the app works as before.
 */
public final class HealthConnectSource {

    public static final String[] PERMISSIONS = {
            "android.permission.health.READ_STEPS", "android.permission.health.READ_HEART_RATE"};
    private static final long WINDOW_MILLIS = 24 * 60 * 60 * 1000L;

    private final Context context;
    private final Platform platform;

    public HealthConnectSource(Context context) {
        this.context = context.getApplicationContext();
        this.platform = isSupported() ? new Platform(this.context) : null;
    }

    public static boolean isSupported() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE;
    }

    public boolean isAvailable() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE || platform == null) {
            return false;
        }
        return platform.manager != null;
    }

    public boolean hasPermissions() {
        for (String permission : PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(context, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    /** Points for the last 24 hours; callbacks run on the main thread. */
    public void readPoints(Consumer<List<TelemetryBatchRequest.Point>> onResult, Consumer<String> onError) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE || !isAvailable()) {
            onError.accept("Health Connect is not available on this device.");
            return;
        }
        platform.readPoints(onResult, onError);
    }

    @RequiresApi(Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
    private static final class Platform {
        private final Context context;
        private final HealthConnectManager manager;

        Platform(Context context) {
            this.context = context;
            this.manager = context.getSystemService(HealthConnectManager.class);
        }

        void readPoints(Consumer<List<TelemetryBatchRequest.Point>> onResult, Consumer<String> onError) {
            Executor main = ContextCompat.getMainExecutor(context);
            Instant now = Instant.now();
            Instant from = now.minusMillis(WINDOW_MILLIS);
            TimeInstantRangeFilter range = new TimeInstantRangeFilter.Builder().setStartTime(from).setEndTime(now).build();
            ReadRecordsRequestUsingFilters<StepsRecord> stepsRequest =
                    new ReadRecordsRequestUsingFilters.Builder<>(StepsRecord.class).setTimeRangeFilter(range).setPageSize(5000).build();
            ReadRecordsRequestUsingFilters<HeartRateRecord> pulseRequest =
                    new ReadRecordsRequestUsingFilters.Builder<>(HeartRateRecord.class).setTimeRangeFilter(range).setPageSize(5000).build();

            manager.readRecords(stepsRequest, main, new Receiver<>(onError, stepsResponse -> {
                List<TelemetryBuckets.Steps> steps = new ArrayList<>();
                for (StepsRecord r : stepsResponse.getRecords()) {
                    steps.add(new TelemetryBuckets.Steps(r.getStartTime().toEpochMilli(), r.getEndTime().toEpochMilli(), r.getCount()));
                }
                manager.readRecords(pulseRequest, main, new Receiver<>(onError, pulseResponse -> {
                    List<TelemetryBuckets.Pulse> pulses = new ArrayList<>();
                    for (HeartRateRecord r : pulseResponse.getRecords()) {
                        for (HeartRateRecord.HeartRateSample s : r.getSamples()) {
                            pulses.add(new TelemetryBuckets.Pulse(s.getTime().toEpochMilli(), s.getBeatsPerMinute()));
                        }
                    }
                    onResult.accept(TelemetryBuckets.build(steps, pulses, from.toEpochMilli(), now.toEpochMilli(), ZoneId.systemDefault()));
                }));
            }));
        }
    }

    @RequiresApi(Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
    private static final class Receiver<T extends android.health.connect.datatypes.Record>
            implements OutcomeReceiver<ReadRecordsResponse<T>, HealthConnectException> {
        private final Consumer<String> onError;
        private final Consumer<ReadRecordsResponse<T>> onResult;

        Receiver(Consumer<String> onError, Consumer<ReadRecordsResponse<T>> onResult) {
            this.onError = onError;
            this.onResult = onResult;
        }

        @Override
        public void onResult(ReadRecordsResponse<T> result) {
            onResult.accept(result);
        }

        @Override
        public void onError(@NonNull HealthConnectException error) {
            onError.accept("Health Connect: " + error.getMessage());
        }
    }
}
