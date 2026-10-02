package com.fitquest.app.ws;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.ApiConfig;
import com.fitquest.app.api.dto.TelemetryDto;
import com.google.gson.Gson;

import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

/**
 * Live telemetry socket. After connect, sends {"token":"&lt;jwt&gt;"}.
 * Callers should fall back to REST polling if this fails.
 */
public class TelemetryWebSocket {

    public interface Listener {
        void onSample(TelemetryDto sample);

        void onStatus(String status);

        void onFailed(String reason);
    }

    private final Gson gson = new Gson();
    private WebSocket socket;
    private boolean opened;

    public void connect(String httpBaseUrl, String jwt, Listener listener) {
        close();
        opened = false;
        String url = ApiConfig.toWebSocketUrl(httpBaseUrl);
        Request request = new Request.Builder().url(url).build();
        listener.onStatus("Connecting WebSocket…");
        socket = ApiClient.http().newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(@NonNull WebSocket webSocket, @NonNull Response response) {
                opened = true;
                String payload = "{\"token\":\"" + (jwt == null ? "" : jwt) + "\"}";
                webSocket.send(payload);
                listener.onStatus("Live socket");
            }

            @Override
            public void onMessage(@NonNull WebSocket webSocket, @NonNull String text) {
                try {
                    TelemetryDto dto = gson.fromJson(text, TelemetryDto.class);
                    if (dto != null) {
                        listener.onSample(dto);
                    }
                } catch (Exception ignored) {
                    listener.onStatus("Live: " + text);
                }
            }

            @Override
            public void onClosing(@NonNull WebSocket webSocket, int code, @NonNull String reason) {
                webSocket.close(1000, null);
                listener.onStatus("Socket closed");
            }

            @Override
            public void onFailure(@NonNull WebSocket webSocket, @NonNull Throwable t, @Nullable Response response) {
                listener.onFailed(t.getMessage() == null ? "WebSocket failed" : t.getMessage());
            }
        });
    }

    public boolean isOpened() {
        return opened;
    }

    public void close() {
        opened = false;
        if (socket != null) {
            socket.close(1000, "bye");
            socket = null;
        }
    }
}
