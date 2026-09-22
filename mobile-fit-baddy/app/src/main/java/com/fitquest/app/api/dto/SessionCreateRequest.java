package com.fitquest.app.api.dto;

public class SessionCreateRequest {
    public int workout_plan_id;

    public SessionCreateRequest(int workoutPlanId) {
        this.workout_plan_id = workoutPlanId;
    }
}
