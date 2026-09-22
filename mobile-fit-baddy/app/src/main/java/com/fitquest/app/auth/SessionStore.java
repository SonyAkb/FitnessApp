package com.fitquest.app.auth;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKeys;

/**
 * Stores JWT and a few session flags. Prefers EncryptedSharedPreferences
 * with a plaintext fallback so emulators without Keystore still run.
 */
public class SessionStore {

    private static final String TAG = "SessionStore";
    private static final String FILE = "fitquest_session";
    private static final String KEY_TOKEN = "access_token";
    private static final String KEY_TOKEN_TYPE = "token_type";
    private static final String KEY_SESSION_ID = "active_session_id";
    private static final String KEY_SESSION_STARTED = "active_session_started";
    private static final String KEY_PLAN_ID = "active_plan_id";
    private static final String KEY_DEVICE_ID = "device_id";
    private static final String KEY_DISPLAY_NAME = "display_name";

    private final SharedPreferences prefs;

    public SessionStore(Context context) {
        prefs = createPrefs(context.getApplicationContext());
    }

    private static SharedPreferences createPrefs(Context context) {
        try {
            String masterKey = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC);
            return EncryptedSharedPreferences.create(
                    FILE,
                    masterKey,
                    context,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
        } catch (Exception e) {
            Log.w(TAG, "Encrypted prefs unavailable, using plaintext fallback", e);
            return context.getSharedPreferences(FILE + "_plain", Context.MODE_PRIVATE);
        }
    }

    public void saveTokens(String accessToken, String tokenType, String displayName) {
        prefs.edit()
                .putString(KEY_TOKEN, accessToken)
                .putString(KEY_TOKEN_TYPE, tokenType == null ? "bearer" : tokenType)
                .putString(KEY_DISPLAY_NAME, displayName)
                .apply();
    }

    public String getAccessToken() {
        return prefs.getString(KEY_TOKEN, null);
    }

    public boolean isLoggedIn() {
        String token = getAccessToken();
        return token != null && !token.isEmpty();
    }

    public String getDisplayName() {
        return prefs.getString(KEY_DISPLAY_NAME, "");
    }

    public void setDisplayName(String name) {
        prefs.edit().putString(KEY_DISPLAY_NAME, name).apply();
    }

    public void clearTokens() {
        prefs.edit()
                .remove(KEY_TOKEN)
                .remove(KEY_TOKEN_TYPE)
                .remove(KEY_SESSION_ID)
                .remove(KEY_SESSION_STARTED)
                .remove(KEY_PLAN_ID)
                .apply();
    }

    public void setActiveSession(int sessionId, int planId) {
        prefs.edit()
                .putInt(KEY_SESSION_ID, sessionId)
                .putInt(KEY_PLAN_ID, planId)
                .putLong(KEY_SESSION_STARTED, System.currentTimeMillis())
                .apply();
    }

    public void clearActiveSession() {
        prefs.edit()
                .remove(KEY_SESSION_ID)
                .remove(KEY_SESSION_STARTED)
                .remove(KEY_PLAN_ID)
                .apply();
    }

    public int getActiveSessionId() {
        return prefs.getInt(KEY_SESSION_ID, -1);
    }

    public int getActivePlanId() {
        return prefs.getInt(KEY_PLAN_ID, -1);
    }

    public long getActiveSessionStartedAt() {
        return prefs.getLong(KEY_SESSION_STARTED, 0L);
    }

    public int elapsedSeconds() {
        long started = getActiveSessionStartedAt();
        if (started <= 0) {
            return 0;
        }
        return (int) Math.max(0, (System.currentTimeMillis() - started) / 1000);
    }

    public void setDeviceId(String deviceId) {
        prefs.edit().putString(KEY_DEVICE_ID, deviceId).apply();
    }

    public String getDeviceId() {
        return prefs.getString(KEY_DEVICE_ID, null);
    }
}
