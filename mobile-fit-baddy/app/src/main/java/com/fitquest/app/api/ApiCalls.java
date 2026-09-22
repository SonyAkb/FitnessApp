package com.fitquest.app.api;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.function.Consumer;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public final class ApiCalls {

    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private ApiCalls() {
    }

    public static <T> void enqueue(Call<T> call, Consumer<T> onSuccess, Consumer<String> onError) {
        call.enqueue(new Callback<T>() {
            @Override
            public void onResponse(Call<T> c, Response<T> response) {
                if (response.isSuccessful()) {
                    MAIN.post(() -> onSuccess.accept(response.body()));
                    return;
                }
                String message = "Request failed (" + response.code() + ")";
                ResponseBody errorBody = response.errorBody();
                if (errorBody != null) {
                    try {
                        String raw = errorBody.string();
                        if (raw != null && !raw.isEmpty()) {
                            message = humanize(raw, response.code());
                        }
                    } catch (IOException ignored) {
                    }
                }
                String finalMessage = message;
                MAIN.post(() -> onError.accept(finalMessage));
            }

            @Override
            public void onFailure(Call<T> c, Throwable t) {
                String msg = t.getMessage() == null ? "Network error. Is the backend running?" : t.getMessage();
                MAIN.post(() -> onError.accept(msg));
            }
        });
    }

    private static String humanize(String raw, int code) {
        String fromJson = parseFastApiDetail(raw);
        if (fromJson != null) {
            return fromJson;
        }
        if (code == 401) {
            return "Session expired. Sign in again.";
        }
        if (code == 404) {
            return "Not found.";
        }
        if (code == 422) {
            return "Check the form: the server rejected a field (422).";
        }
        if (code >= 500) {
            return "Server error. Try again in a moment.";
        }
        return raw.length() > 180 ? raw.substring(0, 180) : raw;
    }

    /** FastAPI: `{ "detail": "..." }` or `{ "detail": [ { "loc", "msg" } ] }`. */
    private static String parseFastApiDetail(String raw) {
        try {
            JSONObject json = new JSONObject(raw);
            Object detail = json.opt("detail");
            if (detail instanceof String) {
                String text = ((String) detail).trim();
                return text.isEmpty() ? null : text;
            }
            if (detail instanceof JSONArray) {
                JSONArray arr = (JSONArray) detail;
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < arr.length(); i++) {
                    JSONObject item = arr.optJSONObject(i);
                    if (item == null) {
                        continue;
                    }
                    String msg = item.optString("msg", "").trim();
                    if (msg.isEmpty()) {
                        continue;
                    }
                    String field = lastLoc(item.optJSONArray("loc"));
                    if (sb.length() > 0) {
                        sb.append('\n');
                    }
                    if (!field.isEmpty()) {
                        sb.append(field).append(": ");
                    }
                    sb.append(msg);
                }
                return sb.length() == 0 ? null : sb.toString();
            }
        } catch (JSONException ignored) {
        }
        return null;
    }

    private static String lastLoc(JSONArray loc) {
        if (loc == null || loc.length() == 0) {
            return "";
        }
        for (int i = loc.length() - 1; i >= 0; i--) {
            String part = loc.optString(i, "");
            if (!part.isEmpty() && !"body".equals(part)) {
                return part;
            }
        }
        return "";
    }
}
