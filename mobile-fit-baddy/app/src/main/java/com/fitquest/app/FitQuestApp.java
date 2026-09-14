package com.fitquest.app;

import android.app.Application;

import com.fitquest.app.api.ApiClient;
import com.fitquest.app.auth.SessionStore;

import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Application singleton: session, Retrofit, and 401 routing.
 */
public class FitQuestApp extends Application {

    private static FitQuestApp instance;
    private SessionStore sessionStore;
    private final CopyOnWriteArrayList<UnauthorizedListener> listeners = new CopyOnWriteArrayList<>();

    public interface UnauthorizedListener {
        void onUnauthorized();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        sessionStore = new SessionStore(this);
        ApiClient.init(this);
    }

    public static FitQuestApp get() {
        return instance;
    }

    public SessionStore session() {
        return sessionStore;
    }

    public void addUnauthorizedListener(UnauthorizedListener listener) {
        listeners.add(listener);
    }

    public void removeUnauthorizedListener(UnauthorizedListener listener) {
        listeners.remove(listener);
    }

    public void notifyUnauthorized() {
        sessionStore.clearTokens();
        for (UnauthorizedListener listener : listeners) {
            listener.onUnauthorized();
        }
    }
}
