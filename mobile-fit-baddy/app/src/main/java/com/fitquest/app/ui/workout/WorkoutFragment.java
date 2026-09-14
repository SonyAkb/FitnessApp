package com.fitquest.app.ui.workout;

import android.app.AlertDialog;
import android.os.Bundle;
import android.text.InputType;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.CompleteSessionRequest;
import com.fitquest.app.api.dto.CreatePlanRequest;
import com.fitquest.app.api.dto.ExerciseDto;
import com.fitquest.app.api.dto.ScheduleCreateRequest;
import com.fitquest.app.api.dto.SessionCreateRequest;
import com.fitquest.app.api.dto.SessionDto;
import com.fitquest.app.api.dto.WorkoutPlanDto;
import com.fitquest.app.auth.SessionStore;
import com.fitquest.app.databinding.FragmentWorkoutBinding;
import com.fitquest.app.databinding.ItemPlanBinding;
import com.fitquest.app.databinding.ItemSessionBinding;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class WorkoutFragment extends Fragment {

    private FragmentWorkoutBinding binding;
    private final List<WorkoutPlanDto> plans = new ArrayList<>();
    private final List<SessionDto> history = new ArrayList<>();
    private PlanAdapter planAdapter;
    private HistoryAdapter historyAdapter;
    private Integer selectedPlanId;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentWorkoutBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        planAdapter = new PlanAdapter();
        historyAdapter = new HistoryAdapter();
        binding.plans.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.plans.setAdapter(planAdapter);
        binding.history.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.history.setAdapter(historyAdapter);

        binding.btnCreatePlan.setOnClickListener(v -> showCreatePlanDialog());
        binding.btnStart.setOnClickListener(v -> startSession());
        binding.btnComplete.setOnClickListener(v -> completeSession());
        binding.btnPinToday.setOnClickListener(v -> pinToday());
        binding.swipe.setOnRefreshListener(this::load);
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
        refreshActiveBanner();
    }

    private void load() {
        showError(null);
        ApiCalls.enqueue(ApiClient.get().getPlans(), list -> {
            plans.clear();
            if (list != null) {
                plans.addAll(list);
            }
            planAdapter.notifyDataSetChanged();
            binding.emptyPlans.setVisibility(plans.isEmpty() ? View.VISIBLE : View.GONE);
            if (binding != null) {
                binding.swipe.setRefreshing(false);
            }
        }, err -> {
            showError(err);
            if (binding != null) {
                binding.swipe.setRefreshing(false);
            }
        });
        ApiCalls.enqueue(ApiClient.get().getHistory(), wrapper -> {
            history.clear();
            if (wrapper != null) {
                history.addAll(wrapper.safeItems());
            }
            historyAdapter.notifyDataSetChanged();
            binding.emptyHistory.setVisibility(history.isEmpty() ? View.VISIBLE : View.GONE);
        }, err -> { /* history optional */ });
        refreshActiveBanner();
    }

    private void refreshActiveBanner() {
        if (binding == null) {
            return;
        }
        SessionStore session = FitQuestApp.get().session();
        boolean active = session.getActiveSessionId() > 0;
        binding.activeCard.setVisibility(active ? View.VISIBLE : View.GONE);
        binding.btnComplete.setEnabled(active);
        if (active) {
            binding.activeText.setText("Quest in progress · " + session.elapsedSeconds() + "s");
        }
    }

    private void pinToday() {
        if (selectedPlanId == null) {
            toast("Pick a plan first");
            return;
        }
        String title = "Today's quest";
        for (WorkoutPlanDto plan : plans) {
            if (selectedPlanId.equals(plan.id) && plan.title != null) {
                title = plan.title;
                break;
            }
        }
        ScheduleCreateRequest body = new ScheduleCreateRequest(
                title,
                OffsetDateTime.now().toString(),
                selectedPlanId,
                null
        );
        setBusy(true);
        ApiCalls.enqueue(ApiClient.get().createSchedule(body), item -> {
            setBusy(false);
            toast("Pinned for today — check the den");
        }, err -> {
            setBusy(false);
            toast(err);
        });
    }

    private void startSession() {
        if (selectedPlanId == null) {
            toast("Pick a plan first (or create one)");
            return;
        }
        setBusy(true);
        ApiCalls.enqueue(ApiClient.get().startSession(new SessionCreateRequest(selectedPlanId)), session -> {
            setBusy(false);
            if (session == null || session.id == null) {
                toast("Session started but no id returned");
                return;
            }
            FitQuestApp.get().session().setActiveSession(session.id, selectedPlanId);
            toast("Quest started — sweat, then complete it");
            refreshActiveBanner();
        }, err -> {
            setBusy(false);
            toast(err);
        });
    }

    private void completeSession() {
        SessionStore store = FitQuestApp.get().session();
        int id = store.getActiveSessionId();
        if (id <= 0) {
            toast("No active quest");
            return;
        }
        setBusy(true);
        int duration = store.elapsedSeconds();
        ApiCalls.enqueue(ApiClient.get().completeSession(id, new CompleteSessionRequest(duration)), session -> {
            setBusy(false);
            store.clearActiveSession();
            toast("Quest complete! Check your fox — XP is incoming.");
            refreshActiveBanner();
            load();
        }, err -> {
            setBusy(false);
            toast(err);
        });
    }

    private void showCreatePlanDialog() {
        LinearLayout column = new LinearLayout(requireContext());
        column.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (16 * getResources().getDisplayMetrics().density);
        column.setPadding(pad, pad / 2, pad, 0);

        EditText title = field("Plan title", "Forest legs");
        EditText exercise = field("Exercise name", "Squats");
        EditText sets = field("Sets", "3");
        sets.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText reps = field("Reps", "10");
        reps.setInputType(InputType.TYPE_CLASS_NUMBER);
        EditText weight = field("Weight kg (optional)", "20");
        weight.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        column.addView(title);
        column.addView(exercise);
        column.addView(sets);
        column.addView(reps);
        column.addView(weight);

        new AlertDialog.Builder(requireContext())
                .setTitle("Craft a quest")
                .setView(column)
                .setPositiveButton("Save plan", (d, w) -> {
                    String planTitle = title.getText().toString().trim();
                    String exName = exercise.getText().toString().trim();
                    if (planTitle.isEmpty() || exName.isEmpty()) {
                        toast("Title and exercise are required");
                        return;
                    }
                    int setCount = parseInt(sets.getText().toString(), 3);
                    int repCount = parseInt(reps.getText().toString(), 10);
                    Double kg = parseDouble(weight.getText().toString());
                    CreatePlanRequest body = new CreatePlanRequest(
                            planTitle,
                            Collections.singletonList(new ExerciseDto(exName, setCount, repCount, kg))
                    );
                    setBusy(true);
                    ApiCalls.enqueue(ApiClient.get().createPlan(body), plan -> {
                        setBusy(false);
                        toast("Plan ready");
                        if (plan != null && plan.id != null) {
                            selectedPlanId = plan.id;
                        }
                        load();
                    }, err -> {
                        setBusy(false);
                        toast(err);
                    });
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private EditText field(String hint, String preset) {
        EditText edit = new EditText(requireContext());
        edit.setHint(hint);
        edit.setText(preset);
        return edit;
    }

    private static int parseInt(String raw, int fallback) {
        try {
            return Integer.parseInt(raw.trim());
        } catch (Exception e) {
            return fallback;
        }
    }

    private static Double parseDouble(String raw) {
        try {
            if (raw == null || raw.trim().isEmpty()) {
                return null;
            }
            return Double.parseDouble(raw.trim());
        } catch (Exception e) {
            return null;
        }
    }

    private void setBusy(boolean busy) {
        if (binding == null) {
            return;
        }
        binding.progress.setVisibility(busy ? View.VISIBLE : View.GONE);
        binding.btnStart.setEnabled(!busy);
        binding.btnCreatePlan.setEnabled(!busy);
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

    private void toast(String msg) {
        Toast.makeText(requireContext(), msg, Toast.LENGTH_LONG).show();
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }

    private class PlanAdapter extends RecyclerView.Adapter<PlanAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemPlanBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            WorkoutPlanDto plan = plans.get(position);
            holder.binding.title.setText(plan.title == null ? "Untitled plan" : plan.title);
            StringBuilder lines = new StringBuilder();
            for (ExerciseDto ex : plan.safeExercises()) {
                if (lines.length() > 0) {
                    lines.append('\n');
                }
                lines.append(ex.summary());
            }
            holder.binding.exercises.setText(lines.length() == 0 ? "No exercises listed" : lines.toString());
            boolean selected = selectedPlanId != null && selectedPlanId.equals(plan.id);
            holder.binding.getRoot().setSelected(selected);
            holder.binding.getRoot().setOnClickListener(v -> {
                selectedPlanId = plan.id;
                notifyDataSetChanged();
            });
        }

        @Override
        public int getItemCount() {
            return plans.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemPlanBinding binding;

            VH(ItemPlanBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }

    private class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemSessionBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            SessionDto session = history.get(position);
            String title = session.plan_name != null ? session.plan_name
                    : (session.title != null ? session.title : "Session #" + session.id);
            holder.binding.title.setText(title);
            String status = session.status == null ? "" : session.status;
            String dur = session.duration_seconds == null ? "" : " · " + session.duration_seconds + "s";
            holder.binding.meta.setText(status + dur);
        }

        @Override
        public int getItemCount() {
            return history.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemSessionBinding binding;

            VH(ItemSessionBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }
}
