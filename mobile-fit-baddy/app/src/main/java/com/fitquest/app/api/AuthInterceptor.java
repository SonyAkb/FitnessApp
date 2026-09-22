package com.fitquest.app.api;

import androidx.annotation.NonNull;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.auth.SessionStore;

import java.io.IOException;

import okhttp3.Interceptor;
import okhttp3.Request;
import okhttp3.Response;

public class AuthInterceptor implements Interceptor {

    private final SessionStore sessionStore;

    public AuthInterceptor(SessionStore sessionStore) {
        this.sessionStore = sessionStore;
    }

    @NonNull
    @Override
    public Response intercept(@NonNull Chain chain) throws IOException {
        Request original = chain.request();
        String path = original.url().encodedPath();
        boolean authEndpoint = path.contains("/auth/login") || path.contains("/auth/register");

        Request.Builder builder = original.newBuilder();
        String token = sessionStore.getAccessToken();
        if (!authEndpoint && token != null && !token.isEmpty()) {
            builder.header("Authorization", "Bearer " + token);
        }

        Response response = chain.proceed(builder.build());
        if (!authEndpoint && response.code() == 401) {
            FitQuestApp app = FitQuestApp.get();
            if (app != null) {
                app.notifyUnauthorized();
            }
        }
        return response;
    }
}
