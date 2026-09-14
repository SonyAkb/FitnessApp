package com.fitquest.app.ui.profile;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.R;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.ApiConfig;
import com.fitquest.app.api.dto.ProfileUpdateRequest;
import com.fitquest.app.api.dto.SubscriptionDto;
import com.fitquest.app.api.dto.UserDto;
import com.fitquest.app.databinding.FragmentProfileBinding;
import com.fitquest.app.ui.AuthActivity;
import com.fitquest.app.ui.telemetry.TelemetryFragment;

public class ProfileFragment extends Fragment {

    private FragmentProfileBinding binding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentProfileBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        binding.inputBaseUrl.getEditText().setText(ApiConfig.getBaseUrl(requireContext()));
        binding.btnSaveProfile.setOnClickListener(v -> saveProfile());
        binding.btnCheckout.setOnClickListener(v -> checkout());
        binding.btnSaveUrl.setOnClickListener(v -> saveUrl());
        binding.btnLogout.setOnClickListener(v -> logout());
        binding.btnLive.setOnClickListener(v ->
                requireActivity().getSupportFragmentManager()
                        .beginTransaction()
                        .replace(R.id.fragmentContainer, new TelemetryFragment())
                        .addToBackStack("telemetry")
                        .commit());
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
    }

    private void load() {
        ApiCalls.enqueue(ApiClient.get().me(), this::bindUser, this::toast);
        ApiCalls.enqueue(ApiClient.get().getSubscription(), this::bindSub, err -> {
            if (binding != null) {
                binding.plan.setText("Plan unknown");
            }
        });
    }

    private void bindUser(UserDto user) {
        if (user == null || binding == null) {
            return;
        }
        set(binding.inputName, user.display_name);
        set(binding.inputGoal, user.goal);
        set(binding.inputWeight, user.weight_kg == null ? "" : String.valueOf(user.weight_kg));
        set(binding.inputLevel, user.fitness_level);
        binding.email.setText(user.email == null ? "" : user.email);
    }

    private void bindSub(SubscriptionDto sub) {
        if (binding == null) {
            return;
        }
        if (sub == null) {
            binding.plan.setText("Free den");
            return;
        }
        String plan = sub.plan == null ? "free" : sub.plan;
        String status = sub.status == null ? "" : " · " + sub.status;
        binding.plan.setText(plan + status);
    }

    private void saveProfile() {
        String name = value(binding.inputName);
        String goal = value(binding.inputGoal);
        String level = value(binding.inputLevel);
        Double weight = null;
        String weightRaw = value(binding.inputWeight);
        if (!TextUtils.isEmpty(weightRaw)) {
            try {
                weight = Double.parseDouble(weightRaw);
            } catch (NumberFormatException e) {
                toast("Weight must be a number");
                return;
            }
        }
        ApiCalls.enqueue(
                ApiClient.get().updateProfile(new ProfileUpdateRequest(name, goal, weight, level)),
                user -> {
                    toast("Profile saved");
                    if (user != null) {
                        FitQuestApp.get().session().setDisplayName(user.display_name);
                        bindUser(user);
                    }
                },
                this::toast
        );
    }

    private void checkout() {
        ApiCalls.enqueue(ApiClient.get().checkout(), sub -> {
            toast("Mock checkout complete");
            bindSub(sub);
        }, this::toast);
    }

    private void saveUrl() {
        String url = value(binding.inputBaseUrl);
        ApiConfig.setBaseUrl(requireContext(), url);
        toast("Base URL saved: " + ApiConfig.getBaseUrl(requireContext()));
    }

    private void logout() {
        FitQuestApp.get().session().clearTokens();
        Intent intent = new Intent(requireContext(), AuthActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
        requireActivity().finish();
    }

    private static void set(com.google.android.material.textfield.TextInputLayout layout, String value) {
        if (layout.getEditText() != null) {
            layout.getEditText().setText(value == null ? "" : value);
        }
    }

    private static String value(com.google.android.material.textfield.TextInputLayout layout) {
        if (layout.getEditText() == null) {
            return "";
        }
        return layout.getEditText().getText().toString().trim();
    }

    private void toast(String msg) {
        Toast.makeText(requireContext(), msg, Toast.LENGTH_LONG).show();
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }
}
