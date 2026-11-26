package com.fitquest.app.workout;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Состояние экрана тренировки. Чистый Java, тестируется без эмулятора. */
public class SessionProgress {

    public enum SetStatus { PENDING, DONE, SKIPPED }

    public static class SetEntry {
        public final int plannedReps;
        public final Double plannedWeightKg;
        public Integer actualReps;
        public Double actualWeightKg;
        public SetStatus status = SetStatus.PENDING;

        public SetEntry(int plannedReps, Double plannedWeightKg) {
            this.plannedReps = plannedReps;
            this.plannedWeightKg = plannedWeightKg;
        }
    }

    public static class ExerciseEntry {
        public final int sessionExerciseId;
        public final String name;
        public final List<SetEntry> sets = new ArrayList<>();

        public ExerciseEntry(String name) {
            this(-1, name);
        }

        public ExerciseEntry(int sessionExerciseId, String name) {
            this.sessionExerciseId = sessionExerciseId;
            this.name = name;
        }
    }

    private final List<ExerciseEntry> exercises;
    private int current = 0;

    public SessionProgress(List<ExerciseEntry> exercises) {
        if (exercises == null || exercises.isEmpty()) {
            throw new IllegalArgumentException("exercises must not be empty");
        }
        this.exercises = Collections.unmodifiableList(new ArrayList<>(exercises));
    }

    public int exerciseCount() { return exercises.size(); }

    /** Индекс с нуля; для подписи «2 из 8» показывай currentIndex() + 1. */
    public int currentIndex() { return current; }

    public ExerciseEntry currentExercise() { return exercises.get(current); }

    public boolean hasNext() { return current < exercises.size() - 1; }

    public boolean hasPrevious() { return current > 0; }

    public boolean next() {
        if (!hasNext()) return false;
        current++;
        return true;
    }

    public boolean previous() {
        if (!hasPrevious()) return false;
        current--;
        return true;
    }

    /** Отметить подход выполненным с фактическими значениями. Можно перезаписать. */
    public void markDone(int setIndex, int reps, Double weightKg) {
        if (reps <= 0) throw new IllegalArgumentException("reps must be > 0");
        SetEntry set = currentExercise().sets.get(setIndex);
        set.actualReps = reps;
        set.actualWeightKg = weightKg;
        set.status = SetStatus.DONE;
    }

    public void skipSet(int setIndex) {
        SetEntry set = currentExercise().sets.get(setIndex);
        if (set.status == SetStatus.PENDING) {
            set.status = SetStatus.SKIPPED;
        }
    }

    /** Все неотмеченные подходы текущего упражнения -> SKIPPED, затем переход к следующему. */
    public void skipExercise() {
        for (SetEntry set : currentExercise().sets) {
            if (set.status == SetStatus.PENDING) {
                set.status = SetStatus.SKIPPED;
            }
        }
        next();
    }

    public int pendingSets() {
        int count = 0;
        for (ExerciseEntry ex : exercises) {
            for (SetEntry set : ex.sets) {
                if (set.status == SetStatus.PENDING) count++;
            }
        }
        return count;
    }

    public int totalSets() {
        int count = 0;
        for (ExerciseEntry ex : exercises) count += ex.sets.size();
        return count;
    }

    /** 0..100: доля подходов, по которым принято решение (выполнен или пропущен). */
    public int progressPercent() {
        int total = totalSets();
        if (total == 0) return 0;
        return (total - pendingSets()) * 100 / total;
    }

    public boolean isAllResolved() { return pendingSets() == 0; }
}