package com.fitquest.app.api.dto;

import java.util.ArrayList;
import java.util.List;

public class SessionDto {
    public Integer id;
    public Integer workout_plan_id;
    public String status;
    public Integer duration_seconds;
    public String started_at;
    public String completed_at;
    public String title;
    public String plan_name;
    public List<SessionExerciseDto> exercises;

    public List<SessionExerciseDto> safeExercises() {
        return exercises == null ? new ArrayList<>() : exercises;
    }
}
