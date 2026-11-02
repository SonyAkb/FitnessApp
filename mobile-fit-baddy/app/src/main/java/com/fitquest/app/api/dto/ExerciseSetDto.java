package com.fitquest.app.api.dto;

public class ExerciseSetDto {
    public Integer id;
    public int set_index;          // с единицы, как на бэкенде
    public int target_reps;
    public Double target_weight_kg;
    public Integer actual_reps;
    public Double actual_weight_kg;
    public String status;          // pending | done | skipped
}
