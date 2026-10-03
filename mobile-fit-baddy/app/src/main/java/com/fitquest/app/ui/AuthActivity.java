package com.fitquest.app.ui;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.LoginRequest;
import com.fitquest.app.api.dto.RegisterRequest;
import com.fitquest.app.api.dto.TokenResponse;
import com.fitquest.app.databinding.ActivityAuthBinding;

public class AuthActivity extends AppCompatActivity {

    private static final int MIN_PASSWORD_LENGTH = 8;

    private ActivityAuthBinding binding;
    private boolean registerMode;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityAuthBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        binding.btnSubmit.setOnClickListener(v -> submit());
        binding.btnToggle.setOnClickListener(v -> {
            registerMode = !registerMode;
            renderMode();
        });
        renderMode();
    }

    private void renderMode() {
        binding.inputName.setVisibility(registerMode ? View.VISIBLE : View.GONE);
        binding.btnSubmit.setText(registerMode ? "Create pack" : "Enter the den");
        binding.btnToggle.setText(registerMode
                ? "Already have a pack? Sign in"
                : "New here? Create a pack");
        binding.title.setText(registerMode ? "Join FitQuest" : "FitQuest");
        binding.subtitle.setText(registerMode
                ? "Name your fox-keeper and start stacking XP"
                : "Train in real life. Your fox levels up with you.");
    }

    private void submit() {
        String email = text(binding.inputEmail.getEditText() == null ? "" : binding.inputEmail.getEditText().getText().toString());
        String password = text(binding.inputPassword.getEditText() == null ? "" : binding.inputPassword.getEditText().getText().toString());
        String name = text(binding.inputName.getEditText() == null ? "" : binding.inputName.getEditText().getText().toString());

        if (TextUtils.isEmpty(email) || TextUtils.isEmpty(password)) {
            toast("Email and password are required");
            return;
        }
        if (registerMode && TextUtils.isEmpty(name)) {
            toast("Give yourself a display name");
            return;
        }
        if (registerMode && password.length() < MIN_PASSWORD_LENGTH) {
            binding.inputPassword.setError("Password must be at least " + MIN_PASSWORD_LENGTH + " characters");
            toast("Password must be at least " + MIN_PASSWORD_LENGTH + " characters");
            return;
        }
        binding.inputPassword.setError(null);

        setLoading(true);
        if (registerMode) {
            ApiCalls.enqueue(
                    ApiClient.get().register(new RegisterRequest(email, password, name)),
                    this::onAuthed,
                    this::onFail
            );
        } else {
            ApiCalls.enqueue(
                    ApiClient.get().login(new LoginRequest(email, password)),
                    this::onAuthed,
                    this::onFail
            );
        }
    }

    private void onAuthed(TokenResponse response) {
        setLoading(false);
        if (response == null || response.access_token == null) {
            toast("Server returned no token");
            return;
        }
        String name = response.user == null ? null : response.user.display_name;
        FitQuestApp.get().session().saveTokens(response.access_token, response.token_type, name);
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }

    private void onFail(String error) {
        setLoading(false);
        toast(error);
    }

    private void setLoading(boolean loading) {
        binding.progress.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnSubmit.setEnabled(!loading);
        binding.btnToggle.setEnabled(!loading);
    }

    private static String text(String value) {
        return value == null ? "" : value.trim();
    }

    private void toast(String msg) {
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
    }
}
