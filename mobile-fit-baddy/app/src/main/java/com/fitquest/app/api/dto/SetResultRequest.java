package com.fitquest.app.api.dto;

public class SetResultRequest {
    public int session_exercise_id;
    public int set_index;            // >= 1
    public Integer actual_reps;      // null при skipped: Gson такие поля не отправляет
    public Double actual_weight_kg;
    public String status;            // "done" | "skipped"

    public SetResultRequest(int sessionExerciseId, int setIndex,
                            Integer actualReps, Double actualWeightKg, String status) {
        this.session_exercise_id = sessionExerciseId;
        this.set_index = setIndex;
        this.actual_reps = actualReps;
        this.actual_weight_kg = actualWeightKg;
        this.status = status;
    }
}
