package com.fitquest.app.ui.quests;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.AchievementDto;
import com.fitquest.app.api.dto.QuestDto;
import com.fitquest.app.databinding.FragmentQuestsBinding;
import com.fitquest.app.databinding.ItemAchievementBinding;
import com.fitquest.app.databinding.ItemQuestBinding;

import java.util.ArrayList;
import java.util.List;

public class QuestsFragment extends Fragment {

    private FragmentQuestsBinding binding;
    private final List<QuestDto> quests = new ArrayList<>();
    private final List<AchievementDto> achievements = new ArrayList<>();
    private QuestAdapter questAdapter;
    private AchievementAdapter achievementAdapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentQuestsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        questAdapter = new QuestAdapter();
        achievementAdapter = new AchievementAdapter();
        binding.questList.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.questList.setAdapter(questAdapter);
        binding.achievementList.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.achievementList.setAdapter(achievementAdapter);
        binding.swipe.setOnRefreshListener(this::load);
    }

    @Override
    public void onResume() {
        super.onResume();
        // Перезагружаем при каждом возврате на экран: завершение тренировки
        // (completeSession -> workout_completed на бэкенде) двигает прогресс квеста,
        // и при заходе сюда он уже будет обновлён.
        load();
    }

    private void load() {
        ApiCalls.enqueue(ApiClient.get().getQuests(), list -> {
            if (binding == null) return;
            quests.clear();
            if (list != null) quests.addAll(list);
            questAdapter.notifyDataSetChanged();
            binding.questsEmpty.setVisibility(quests.isEmpty() ? View.VISIBLE : View.GONE);
            binding.swipe.setRefreshing(false);
            binding.error.setVisibility(View.GONE);
        }, err -> showError(err));
        ApiCalls.enqueue(ApiClient.get().getAchievements(), list -> {
            if (binding == null) return;
            achievements.clear();
            if (list != null) achievements.addAll(list);
            achievementAdapter.notifyDataSetChanged();
            binding.achievementsEmpty.setVisibility(achievements.isEmpty() ? View.VISIBLE : View.GONE);
            binding.swipe.setRefreshing(false);
        }, err -> { /* достижения вторичны, не перекрываем ошибку квестов */ });
    }

    private void showError(String error) {
        if (binding == null) return;
        binding.error.setVisibility(View.VISIBLE);
        binding.error.setText(error);
        binding.swipe.setRefreshing(false);
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }

    private class QuestAdapter extends RecyclerView.Adapter<QuestAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemQuestBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            QuestDto q = quests.get(position);
            holder.binding.title.setText(q.title == null ? "Quest" : q.title);
            int progress = q.progress == null ? 0 : q.progress;
            int target = q.target == null ? 1 : Math.max(1, q.target);
            holder.binding.progressBar.setMax(target);
            holder.binding.progressBar.setProgress(Math.min(progress, target));
            holder.binding.progressText.setText(progress + "/" + target);
            String period = q.period == null ? "" : capitalize(q.period);
            String reward = q.xp_reward == null ? "" : " · +" + q.xp_reward + " XP";
            String status = q.isCompleted() ? "Done" : "In progress";
            holder.binding.meta.setText(status + " · " + period + reward);
        }

        @Override
        public int getItemCount() {
            return quests.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemQuestBinding binding;
            VH(ItemQuestBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }

    private class AchievementAdapter extends RecyclerView.Adapter<AchievementAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemAchievementBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            AchievementDto a = achievements.get(position);
            holder.binding.title.setText(a.title == null ? a.code : a.title);
            holder.binding.date.setText(a.earned_at == null ? "Earned" : formatDateTime(a.earned_at));
            holder.binding.xp.setText(a.xp_reward == null ? "" : "+" + a.xp_reward + " XP");
        }

        @Override
        public int getItemCount() {
            return achievements.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemAchievementBinding binding;
            VH(ItemAchievementBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }

    private static String capitalize(String s) {
        return s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1).toLowerCase();
    }

    private static String formatDateTime(String iso) {
        String s = iso.replace("T", " ");
        int dot = s.indexOf('.');
        if (dot > 0) s = s.substring(0, dot);
        return s.length() > 16 ? s.substring(0, 16) : s;
    }
}