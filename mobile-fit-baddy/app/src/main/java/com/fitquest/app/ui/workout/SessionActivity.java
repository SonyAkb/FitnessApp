package com.fitquest.app.ui.workout;

import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.CompleteSessionRequest;
import com.fitquest.app.api.dto.SessionExerciseDto;
import com.fitquest.app.api.dto.SetResultRequest;
import com.fitquest.app.auth.SessionStore;
import com.fitquest.app.databinding.ActivitySessionBinding;
import com.fitquest.app.databinding.ItemSetBinding;
import com.fitquest.app.workout.RestTimer;
import com.fitquest.app.workout.SessionProgress;
import com.fitquest.app.workout.SessionProgress.ExerciseEntry;
import com.fitquest.app.workout.SessionProgress.SetEntry;
import com.fitquest.app.workout.SessionProgress.SetStatus;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.util.List;
import java.util.Locale;

/** AND-11: экран выполнения тренировки с чек-листом подходов. */
public class SessionActivity extends AppCompatActivity {

    private static final long REST_TICK_MS = 250;

    private ActivitySessionBinding binding;
    private SessionViewModel vm;
    private SetAdapter adapter;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable restTick = new Runnable() {
        @Override
        public void run() {
            vm.restTimer.tick();
            renderRest();
            if (vm.restTimer.getState() == RestTimer.State.RUNNING) {
                handler.postDelayed(this, REST_TICK_MS);
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivitySessionBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        vm = new ViewModelProvider(this).get(SessionViewModel.class);
        SessionStore store = FitQuestApp.get().session();
        if (!vm.isInitialized()) {
            String json = store.getActiveExercisesJson();
            if (json != null) {
                List<SessionExerciseDto> list = new Gson().fromJson(
                        json, new TypeToken<List<SessionExerciseDto>>() { }.getType());
                if (list != null) {
                    vm.init(list);
                }
            }
        }
        if (!vm.isInitialized() || store.getActiveSessionId() <= 0) {
            toast("No exercises in this session (check the backend response)");
            finish();
            return;
        }

        adapter = new SetAdapter();
        binding.sets.setLayoutManager(new LinearLayoutManager(this));
        binding.sets.setAdapter(adapter);

        binding.btnPrev.setOnClickListener(v -> {
            vm.progress().previous();
            renderAll();
        });
        binding.btnNext.setOnClickListener(v -> {
            vm.progress().next();
            renderAll();
        });
        binding.btnSkipExercise.setOnClickListener(v -> skipExercise());
        binding.btnFinish.setOnClickListener(v -> confirmFinish());

        binding.btnRest30.setOnClickListener(v -> startRest(30));
        binding.btnRest60.setOnClickListener(v -> startRest(60));
        binding.btnRest90.setOnClickListener(v -> startRest(90));
        binding.btnRest120.setOnClickListener(v -> startRest(120));
        binding.btnRestPlus30.setOnClickListener(v -> {
            vm.restTimer.addSeconds(RestTimer.EXTRA_SECONDS);
            renderRest();
        });
        binding.btnRestSkip.setOnClickListener(v -> {
            vm.restTimer.skip();
            handler.removeCallbacks(restTick);
            renderRest();
        });
        binding.btnRestPause.setOnClickListener(v -> {
            if (vm.restTimer.getState() == RestTimer.State.PAUSED) {
                vm.restTimer.resume();
                handler.removeCallbacks(restTick);
                handler.post(restTick);
            } else {
                vm.restTimer.pause();
                handler.removeCallbacks(restTick);
            }
            renderRest();
        });

        renderAll();
    }

    @Override
    protected void onStart() {
        super.onStart();
        if (vm == null || !vm.isInitialized()) {
            return;
        }
        vm.restTimer.setListener(this::vibrateEnd);
        handler.removeCallbacks(restTick);
        handler.post(restTick);
    }

    @Override
    protected void onStop() {
        // ViewModel живёт дольше Activity: отписываемся, чтобы не держать её в памяти.
        if (vm != null) {
            vm.restTimer.setListener(null);
        }
        handler.removeCallbacks(restTick);
        super.onStop();
    }

    // ------------------------------------------------------------------
    // Действия
    // ------------------------------------------------------------------

    private void markDone(int setIndex, int reps, Double weightKg) {
        ExerciseEntry ex = vm.progress().currentExercise();
        vm.progress().markDone(setIndex, reps, weightKg);
        postSet(ex, setIndex, SetStatus.DONE, reps, weightKg);
        adapter.notifyItemChanged(setIndex);
        renderHeader();
        startRest(vm.restSeconds); // отметка подхода запускает таймер отдыха (AND-12)
    }

    private void skipSet(int setIndex) {
        ExerciseEntry ex = vm.progress().currentExercise();
        vm.progress().skipSet(setIndex);
        postSet(ex, setIndex, SetStatus.SKIPPED, null, null);
        adapter.notifyItemChanged(setIndex);
        renderHeader();
    }

    private void skipExercise() {
        ExerciseEntry ex = vm.progress().currentExercise();
        for (int i = 0; i < ex.sets.size(); i++) {
            if (ex.sets.get(i).status == SetStatus.PENDING) {
                postSet(ex, i, SetStatus.SKIPPED, null, null);
            }
        }
        vm.progress().skipExercise();
        renderAll();
    }

    private void postSet(ExerciseEntry ex, int setIndex, SetStatus status, Integer reps, Double kg) {
        int sessionId = FitQuestApp.get().session().getActiveSessionId();
        // На бэкенде set_index считается с 1 (SetLogIn: ge=1).
        SetResultRequest body = new SetResultRequest(
                ex.sessionExerciseId, setIndex + 1, reps, kg,
                status == SetStatus.DONE ? "done" : "skipped");
        ApiCalls.enqueue(ApiClient.get().postSet(sessionId, body),
                result -> { /* состояние уже обновлено локально */ },
                err -> toast("Set not saved: " + err));
    }

    private void confirmFinish() {
        int pending = vm.progress().pendingSets();
        if (pending == 0) {
            finishSession();
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle("Finish quest?")
                .setMessage(pending + " set(s) are not marked. They will be saved as skipped.")
                .setPositiveButton("Finish", (d, w) -> finishSession())
                .setNegativeButton("Keep going", null)
                .show();
    }

    private void finishSession() {
        SessionStore store = FitQuestApp.get().session();
        int id = store.getActiveSessionId();
        if (id <= 0) {
            finish();
            return;
        }
        binding.btnFinish.setEnabled(false);
        ApiCalls.enqueue(
                ApiClient.get().completeSession(id, new CompleteSessionRequest(store.elapsedSeconds())),
                session -> {
                    store.clearActiveSession();
                    toast("Quest complete! Check your fox — XP is incoming.");
                    finish();
                },
                err -> {
                    toast(err);
                    binding.btnFinish.setEnabled(true);
                });
    }

    // ------------------------------------------------------------------
    // Отрисовка
    // ------------------------------------------------------------------

    private void renderAll() {
        renderHeader();
        adapter.notifyDataSetChanged();
        renderRest();
    }

    private void renderHeader() {
        SessionProgress p = vm.progress();
        binding.exerciseCounter.setText(String.format(Locale.US, "Exercise %d of %d",
                p.currentIndex() + 1, p.exerciseCount()));
        binding.exerciseName.setText(p.currentExercise().name);
        binding.sessionProgress.setProgress(p.progressPercent());
        binding.btnPrev.setEnabled(p.hasPrevious());
        binding.btnNext.setEnabled(p.hasNext());
    }

    private void startRest(int seconds) {
        vm.restSeconds = seconds;
        vm.restTimer.start(seconds);
        handler.removeCallbacks(restTick);
        handler.post(restTick);
    }

    private void renderRest() {
        RestTimer.State state = vm.restTimer.getState();
        boolean active = state == RestTimer.State.RUNNING || state == RestTimer.State.PAUSED;
        binding.restControls.setVisibility(active ? View.VISIBLE : View.GONE);
        if (state == RestTimer.State.IDLE) {
            binding.restTime.setText("--:--");
        } else if (state == RestTimer.State.FINISHED) {
            binding.restTime.setText("Go!");
        } else {
            int sec = vm.restTimer.remainingSeconds();
            binding.restTime.setText(String.format(Locale.US, "%d:%02d", sec / 60, sec % 60));
        }
        binding.btnRestPause.setText(state == RestTimer.State.PAUSED ? "Resume" : "Pause");
    }

    private void vibrateEnd() {
        Vibrator vibrator = getSystemService(Vibrator.class);
        if (vibrator != null && vibrator.hasVibrator()) {
            vibrator.vibrate(VibrationEffect.createWaveform(new long[]{0, 300, 150, 300}, -1));
        }
    }

    private void toast(String msg) {
        Toast.makeText(FitQuestApp.get(), msg, Toast.LENGTH_LONG).show();
    }

    private static String formatKg(Double kg) {
        if (kg == null) {
            return "";
        }
        return kg == Math.rint(kg) ? String.valueOf(kg.longValue()) : String.valueOf(kg);
    }

    // ------------------------------------------------------------------
    // Чек-лист подходов
    // ------------------------------------------------------------------

    private class SetAdapter extends RecyclerView.Adapter<SetAdapter.VH> {

        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemSetBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public int getItemCount() {
            return vm.progress().currentExercise().sets.size();
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            SetEntry set = vm.progress().currentExercise().sets.get(position);
            ItemSetBinding b = holder.binding;
            boolean pending = set.status == SetStatus.PENDING;

            String plan = set.plannedReps + " reps"
                    + (set.plannedWeightKg == null ? "" : " @ " + formatKg(set.plannedWeightKg) + " kg");
            b.setTitle.setText("Set " + (position + 1) + " · plan " + plan);
            b.setStatus.setText(set.status == SetStatus.DONE ? "✓ done"
                    : set.status == SetStatus.SKIPPED ? "skipped" : "");

            if (set.status == SetStatus.DONE) {
                b.editReps.setText(String.valueOf(set.actualReps));
                b.editWeight.setText(formatKg(set.actualWeightKg));
            } else if (pending) {
                b.editReps.setText(String.valueOf(set.plannedReps));
                b.editWeight.setText(formatKg(set.plannedWeightKg));
            } else {
                b.editReps.setText("");
                b.editWeight.setText("");
            }

            b.editReps.setEnabled(pending);
            b.editWeight.setEnabled(pending);
            b.btnSetDone.setEnabled(pending);
            b.btnSetSkip.setEnabled(pending);

            b.btnSetDone.setOnClickListener(v -> {
                int pos = holder.getBindingAdapterPosition();
                if (pos == RecyclerView.NO_POSITION) {
                    return;
                }
                int reps;
                try {
                    reps = Integer.parseInt(b.editReps.getText().toString().trim());
                } catch (NumberFormatException e) {
                    reps = 0;
                }
                if (reps <= 0) {
                    toast("Enter the number of reps");
                    return;
                }
                Double kg = null;
                String raw = b.editWeight.getText().toString().trim().replace(',', '.');
                if (!raw.isEmpty()) {
                    try {
                        kg = Double.parseDouble(raw);
                    } catch (NumberFormatException e) {
                        toast("Weight must be a number");
                        return;
                    }
                }
                markDone(pos, reps, kg);
            });
            b.btnSetSkip.setOnClickListener(v -> {
                int pos = holder.getBindingAdapterPosition();
                if (pos != RecyclerView.NO_POSITION) {
                    skipSet(pos);
                }
            });
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemSetBinding binding;

            VH(ItemSetBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }
}
