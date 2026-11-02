package com.fitquest.app.ui.workout;

import androidx.lifecycle.ViewModel;

import com.fitquest.app.api.dto.ExerciseSetDto;
import com.fitquest.app.api.dto.SessionExerciseDto;
import com.fitquest.app.workout.RestTimer;
import com.fitquest.app.workout.SessionProgress;

import java.util.ArrayList;
import java.util.List;

/** Держит состояние тренировки между поворотами экрана. */
public class SessionViewModel extends ViewModel {

    public static final int DEFAULT_REST_SECONDS = 60;

    private SessionProgress progress;
    public final RestTimer restTimer = RestTimer.system();
    public int restSeconds = DEFAULT_REST_SECONDS;

    public boolean isInitialized() {
        return progress != null;
    }

    public SessionProgress progress() {
        return progress;
    }

    public void init(List<SessionExerciseDto> dtos) {
        List<SessionProgress.ExerciseEntry> list = new ArrayList<>();
        for (SessionExerciseDto dto : dtos) {
            int id = dto.id == null ? -1 : dto.id;
            SessionProgress.ExerciseEntry entry = new SessionProgress.ExerciseEntry(
                    id, dto.name == null ? "Exercise" : dto.name);
            if (dto.sets != null) {
                for (ExerciseSetDto s : dto.sets) {
                    SessionProgress.SetEntry set =
                            new SessionProgress.SetEntry(s.target_reps, s.target_weight_kg);
                    if ("done".equals(s.status) && s.actual_reps != null && s.actual_reps > 0) {
                        set.actualReps = s.actual_reps;
                        set.actualWeightKg = s.actual_weight_kg;
                        set.status = SessionProgress.SetStatus.DONE;
                    } else if ("skipped".equals(s.status)) {
                        set.status = SessionProgress.SetStatus.SKIPPED;
                    }
                    entry.sets.add(set);
                }
            }
            if (!entry.sets.isEmpty()) {
                list.add(entry);
            }
        }
        if (!list.isEmpty()) {
            progress = new SessionProgress(list);
        }
    }
}
