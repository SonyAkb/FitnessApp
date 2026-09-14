package com.fitquest.app.api.dto;

import java.util.ArrayList;
import java.util.List;

public class WorkoutPlanDto {
    public Integer id;
    public String title;
    public List<ExerciseDto> exercises;

    public List<ExerciseDto> safeExercises() {
        return exercises == null ? new ArrayList<>() : exercises;
    }
}
