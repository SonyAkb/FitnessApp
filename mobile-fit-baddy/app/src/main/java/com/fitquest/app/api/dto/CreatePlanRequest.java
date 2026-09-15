package com.fitquest.app.api.dto;

import java.util.List;

public class CreatePlanRequest {
    public String title;
    public List<ExerciseDto> exercises;

    public CreatePlanRequest(String title, List<ExerciseDto> exercises) {
        this.title = title;
        this.exercises = exercises;
    }
}
