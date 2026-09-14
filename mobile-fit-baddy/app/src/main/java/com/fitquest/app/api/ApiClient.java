package com.fitquest.app.api;

import android.content.Context;

import com.fitquest.app.FitQuestApp;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public final class ApiClient {

    private static FitQuestApi api;
    private static OkHttpClient httpClient;
    private static Context appContext;

    private ApiClient() {
    }

    public static void init(Context context) {
        appContext = context.getApplicationContext();
        reset();
    }

    public static synchronized FitQuestApi get() {
        if (api == null) {
            reset();
        }
        return api;
    }

    public static synchronized OkHttpClient http() {
        if (httpClient == null) {
            reset();
        }
        return httpClient;
    }

    public static synchronized void reset() {
        HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
        logging.setLevel(HttpLoggingInterceptor.Level.BASIC);

        httpClient = new OkHttpClient.Builder()
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .addInterceptor(new AuthInterceptor(FitQuestApp.get().session()))
                .addInterceptor(logging)
                .build();

        String base = ApiConfig.getBaseUrl(appContext != null ? appContext : FitQuestApp.get()) + "/";
        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl(base)
                .client(httpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
        api = retrofit.create(FitQuestApi.class);
    }
}
