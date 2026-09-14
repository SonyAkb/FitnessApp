package com.fitquest.app.ui;

import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.R;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.UserDto;

public class SplashActivity extends AppCompatActivity {

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        if (!FitQuestApp.get().session().isLoggedIn()) {
            goAuth();
            return;
        }

        ApiCalls.enqueue(ApiClient.get().me(), (UserDto user) -> {
            if (user != null && user.display_name != null) {
                FitQuestApp.get().session().setDisplayName(user.display_name);
            }
            goMain();
        }, error -> goAuth());
    }

    private void goAuth() {
        startActivity(new Intent(this, AuthActivity.class));
        finish();
    }

    private void goMain() {
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }
}
