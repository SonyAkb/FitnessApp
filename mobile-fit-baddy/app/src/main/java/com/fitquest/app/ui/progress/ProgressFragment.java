package com.fitquest.app.ui.progress;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.DashboardSummaryDto;
import com.fitquest.app.api.dto.RecommendationDto;
import com.fitquest.app.databinding.FragmentProgressBinding;
import com.fitquest.app.ui.UiFormat;

public class ProgressFragment extends Fragment {

    private FragmentProgressBinding binding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentProgressBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        binding.swipe.setOnRefreshListener(this::load);
        binding.btnRecommend.setOnClickListener(v -> loadRecommend());
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
    }

    private void load() {
        showError(null);
        ApiCalls.enqueue(ApiClient.get().getDashboard(), this::bind, err -> {
            showError(err);
            binding.swipe.setRefreshing(false);
        });
        loadRecommend();
    }

    private void loadRecommend() {
        ApiCalls.enqueue(ApiClient.get().getRecommendation(), rec -> {
            if (binding == null) {
                return;
            }
            bindRec(rec);
        }, err -> {
            if (binding != null) {
                binding.recommend.setText("Coach is quiet right now. " + err);
            }
        });
    }

    private void bind(DashboardSummaryDto summary) {
        if (binding == null) {
            return;
        }
        binding.swipe.setRefreshing(false);
        if (summary == null) {
            showError("Empty dashboard");
            return;
        }
        binding.completed.setText(UiFormat.dash(summary.completed_workouts_count));
        binding.streak.setText(UiFormat.dash(summary.current_streak_days));
        binding.xp.setText(UiFormat.dash(summary.xp));
        binding.level.setText(UiFormat.dash(summary.level));
        binding.mood.setText(summary.mood == null ? "idle" : summary.mood);
        binding.heart.setText(UiFormat.dash(summary.last_heart_rate));
        binding.steps.setText(UiFormat.dash(summary.last_steps));
        binding.today.setText(UiFormat.todayTitle(summary));
    }

    private void bindRec(RecommendationDto rec) {
        if (rec == null || rec.text == null) {
            binding.recommend.setText("No tip yet — finish a workout first.");
            return;
        }
        String when = rec.created_at == null ? "" : "\n" + rec.created_at;
        binding.recommend.setText(rec.text + when);
    }

    private void showError(String error) {
        if (binding == null) {
            return;
        }
        binding.error.setVisibility(error == null ? View.GONE : View.VISIBLE);
        if (error != null) {
            binding.error.setText(error);
        }
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }
}
