package com.fitquest.app.api.dto;

import java.util.List;

public class SessionExerciseDto {
    public Integer id;          // session_exercise_id
    public String name;
    public Integer order_index;
    public String status;
    public List<ExerciseSetDto> sets;
}
