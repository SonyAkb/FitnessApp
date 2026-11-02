package com.fitquest.app.ui.workout;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
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
import com.fitquest.app.api.dto.SessionExerciseDto;
import com.fitquest.app.api.dto.WorkoutPlanDto;
import com.fitquest.app.auth.SessionStore;
import com.fitquest.app.databinding.FragmentWorkoutBinding;
import com.fitquest.app.databinding.ItemPlanBinding;
import com.fitquest.app.databinding.ItemSessionBinding;
import com.fitquest.app.workout.RestTimer;
import com.google.gson.Gson;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

public class WorkoutFragment extends Fragment {

    private static final long REST_TICK_MS = 250;

    private FragmentWorkoutBinding binding;
    private final List<WorkoutPlanDto> plans = new ArrayList<>();
    private final List<SessionDto> history = new ArrayList<>();
    private PlanAdapter planAdapter;
    private HistoryAdapter historyAdapter;
    private Integer selectedPlanId;

    // --- AND-12: rest timer. Логика в RestTimer, здесь только отображение. ---
    private final RestTimer restTimer = RestTimer.system();
    private final Handler restHandler = new Handler(Looper.getMainLooper());
    private final Runnable restTick = new Runnable() {
        @Override
        public void run() {
            restTimer.tick();
            renderRest();
            if (restTimer.getState() == RestTimer.State.RUNNING) {
                restHandler.postDelayed(this, REST_TICK_MS);
            }
        }
    };

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
        // AND-11: баннер активной сессии открывает экран тренировки
        binding.activeCard.setOnClickListener(v -> openSessionScreen());

        setupRestTimer();
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
        refreshActiveBanner();
        // Таймер мог дотикать, пока экран был свёрнут: проверим и возобновим цикл тиков.
        restHandler.removeCallbacks(restTick);
        restHandler.post(restTick);
    }

    @Override
    public void onPause() {
        restHandler.removeCallbacks(restTick);
        super.onPause();
    }

    // ------------------------------------------------------------------
    // Rest timer
    // ------------------------------------------------------------------

    private void setupRestTimer() {
        restTimer.setListener(this::vibrateEnd);

        binding.btnRest30.setOnClickListener(v -> startRest(30));
        binding.btnRest60.setOnClickListener(v -> startRest(60));
        binding.btnRest90.setOnClickListener(v -> startRest(90));
        binding.btnRest120.setOnClickListener(v -> startRest(120));

        binding.btnRestPlus30.setOnClickListener(v -> {
            restTimer.addSeconds(RestTimer.EXTRA_SECONDS);
            renderRest();
        });
        binding.btnRestSkip.setOnClickListener(v -> {
            restTimer.skip();
            restHandler.removeCallbacks(restTick);
            renderRest();
        });
        binding.btnRestPause.setOnClickListener(v -> {
            if (restTimer.getState() == RestTimer.State.PAUSED) {
                restTimer.resume();
                restHandler.removeCallbacks(restTick);
                restHandler.post(restTick);
            } else {
                restTimer.pause();
                restHandler.removeCallbacks(restTick);
            }
            renderRest();
        });

        renderRest();
    }

    private void startRest(int seconds) {
        restTimer.start(seconds);
        restHandler.removeCallbacks(restTick);
        restHandler.post(restTick);
    }

    private void renderRest() {
        if (binding == null) {
            return;
        }
        RestTimer.State state = restTimer.getState();
        boolean active = state == RestTimer.State.RUNNING || state == RestTimer.State.PAUSED;
        binding.restControls.setVisibility(active ? View.VISIBLE : View.GONE);

        if (state == RestTimer.State.IDLE) {
            binding.restTime.setText("--:--");
        } else if (state == RestTimer.State.FINISHED) {
            binding.restTime.setText("Go!");
        } else {
            int sec = restTimer.remainingSeconds();
            binding.restTime.setText(String.format(Locale.US, "%d:%02d", sec / 60, sec % 60));
        }
        binding.btnRestPause.setText(state == RestTimer.State.PAUSED ? "Resume" : "Pause");
    }

    private void vibrateEnd() {
        Context context = getContext();
        if (context == null) {
            return;
        }
        Vibrator vibrator = context.getSystemService(Vibrator.class);
        if (vibrator != null && vibrator.hasVibrator()) {
            vibrator.vibrate(VibrationEffect.createWaveform(new long[]{0, 300, 150, 300}, -1));
        }
    }

    // ------------------------------------------------------------------
    // Workout screen
    // ------------------------------------------------------------------

    private void load() {
        showError(null);
        ApiCalls.enqueue(ApiClient.get().getPlans(), list -> {
            if (binding == null) {
                return;
            }
            plans.clear();
            if (list != null) {
                plans.addAll(list);
            }
            planAdapter.notifyDataSetChanged();
            binding.emptyPlans.setVisibility(plans.isEmpty() ? View.VISIBLE : View.GONE);
            binding.swipe.setRefreshing(false);
        }, err -> {
            showError(err);
            if (binding != null) {
                binding.swipe.setRefreshing(false);
            }
        });
        ApiCalls.enqueue(ApiClient.get().getHistory(), wrapper -> {
            if (binding == null) {
                return;
            }
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
            List<SessionExerciseDto> exercises = session.safeExercises();
            FitQuestApp.get().session().setActiveExercisesJson(new Gson().toJson(exercises));
            refreshActiveBanner();
            if (exercises.isEmpty()) {
                toast("Quest started, but the plan has no exercises — use Complete");
            } else {
                openSessionScreen();
            }
        }, err -> {
            setBusy(false);
            toast(err);
        });
    }

    private void openSessionScreen() {
        startActivity(new Intent(requireContext(), SessionActivity.class));
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
        Context context = getContext();
        if (context != null) {
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show();
        }
    }

    @Override
    public void onDestroyView() {
        restHandler.removeCallbacks(restTick);
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
