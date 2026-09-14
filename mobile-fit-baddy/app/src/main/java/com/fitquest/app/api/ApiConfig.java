package com.fitquest.app.api;

import android.content.Context;
import android.content.SharedPreferences;

import com.fitquest.app.BuildConfig;

/**
 * Backend origin. Emulator default is 10.0.2.2 (host loopback).
 * Physical devices must use the LAN IP of the machine running Docker.
 */
public final class ApiConfig {

    public static final String PREFS = "fitquest_config";
    public static final String KEY_BASE_URL = "base_url";
    public static final String DEFAULT_BASE_URL = BuildConfig.API_BASE_URL;

    private ApiConfig() {
    }

    public static String getBaseUrl(Context context) {
        SharedPreferences prefs = context.getApplicationContext()
                .getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String stored = prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL);
        if (stored == null || stored.trim().isEmpty()) {
            return DEFAULT_BASE_URL;
        }
        return stored.trim().replaceAll("/+$", "");
    }

    public static void setBaseUrl(Context context, String url) {
        String clean = url == null ? DEFAULT_BASE_URL : url.trim().replaceAll("/+$", "");
        if (clean.isEmpty()) {
            clean = DEFAULT_BASE_URL;
        }
        context.getApplicationContext()
                .getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_BASE_URL, clean)
                .apply();
        ApiClient.reset();
    }

    public static String toWebSocketUrl(String httpBase) {
        String base = httpBase.replaceAll("/+$", "");
        if (base.startsWith("https://")) {
            return "wss://" + base.substring("https://".length()) + "/api/v1/telemetry/ws";
        }
        if (base.startsWith("http://")) {
            return "ws://" + base.substring("http://".length()) + "/api/v1/telemetry/ws";
        }
        return "ws://" + base + "/api/v1/telemetry/ws";
    }
}
