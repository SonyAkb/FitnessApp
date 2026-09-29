package com.fitquest.app.ui.home;

import android.graphics.drawable.AnimationDrawable;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.fitquest.app.R;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.DashboardSummaryDto;
import com.fitquest.app.api.dto.PetDto;
import com.fitquest.app.api.dto.TelemetryDto;
import com.fitquest.app.databinding.FragmentHomeBinding;
import com.fitquest.app.ui.MainActivity;
import com.fitquest.app.ui.UiFormat;
import com.fitquest.app.ui.telemetry.TelemetryFragment;

public class HomeFragment extends Fragment {

    private FragmentHomeBinding binding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentHomeBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        binding.swipe.setOnRefreshListener(this::load);
        binding.btnStartQuest.setOnClickListener(v -> {
            if (getActivity() instanceof MainActivity) {
                ((MainActivity) getActivity()).openWorkoutTab();
            }
        });
        binding.btnLiveWatch.setOnClickListener(v ->
                requireActivity().getSupportFragmentManager()
                        .beginTransaction()
                        .replace(R.id.fragmentContainer, new TelemetryFragment())
                        .addToBackStack("telemetry")
                        .commit());
        binding.fox.setOnClickListener(v -> load());
        startFoxAnimation();
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
    }

    private void load() {
        showError(null);
        ApiCalls.enqueue(ApiClient.get().getPet(), this::bindPet, this::showError);
        ApiCalls.enqueue(ApiClient.get().getDashboard(), this::bindDashboard, this::showError);
        ApiCalls.enqueue(ApiClient.get().getLatestTelemetry(), this::bindTelemetry, err -> {
            // Telemetry may be empty before simulate — not fatal on home.
            binding.heart.setText("♥ —");
            binding.steps.setText("steps —");
        });
        ApiCalls.enqueue(ApiClient.get().getSchedule(), list -> {
            if (binding == null || list == null || list.isEmpty()) {
                return;
            }
            if ("No quest on the board yet".equals(binding.todayQuest.getText().toString())
                    || "Loading…".equals(binding.todayQuest.getText().toString())) {
                String title = list.get(0).title == null ? "Today's quest is ready" : list.get(0).title;
                binding.todayQuest.setText(title);
            }
        }, err -> { /* optional */ });
        binding.swipe.setRefreshing(false);
    }

    private void bindPet(PetDto pet) {
        if (pet == null || binding == null) {
            return;
        }
        String name = pet.name == null ? "Fox" : pet.name;
        binding.foxName.setText(name);
        binding.fox.setImageResource(UiFormat.foxAnimationForMood(pet.mood));
        startFoxAnimation();
        binding.mood.setText(UiFormat.moodLine(pet.mood));
        int xp = pet.xp == null ? 0 : pet.xp;
        int level = pet.level == null ? 1 : pet.level;
        binding.level.setText("Lv " + level);
        binding.xp.setText(xp + " XP");
        binding.xpBar.setProgress(Math.min(100, xp % 100));
        binding.energy.setText("Energy " + UiFormat.dash(pet.energy));
        binding.streak.setText((pet.streak_days == null ? 0 : pet.streak_days) + " day streak");
    }

    private void startFoxAnimation() {
        if (binding == null) {
            return;
        }
        if (binding.fox.getDrawable() instanceof AnimationDrawable) {
            ((AnimationDrawable) binding.fox.getDrawable()).start();
        }
    }

    private void bindDashboard(DashboardSummaryDto summary) {
        if (summary == null || binding == null) {
            return;
        }
        binding.todayQuest.setText(UiFormat.todayTitle(summary));
        if (summary.last_heart_rate != null) {
            binding.heart.setText("♥ " + summary.last_heart_rate);
        }
        if (summary.last_steps != null) {
            binding.steps.setText(summary.last_steps + " steps");
        }
        if (summary.current_streak_days != null) {
            binding.streak.setText(summary.current_streak_days + " day streak");
        }
        binding.completed.setText(UiFormat.dash(summary.completed_workouts_count) + " quests done");
    }

    private void bindTelemetry(TelemetryDto telemetry) {
        if (telemetry == null || binding == null) {
            return;
        }
        binding.heart.setText("♥ " + UiFormat.dash(telemetry.heart_rate));
        binding.steps.setText(UiFormat.dash(telemetry.steps) + " steps");
    }

    private void showError(String error) {
        if (binding == null) {
            return;
        }
        if (error == null) {
            binding.error.setVisibility(View.GONE);
            return;
        }
        binding.error.setVisibility(View.VISIBLE);
        binding.error.setText(error);
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }
}
