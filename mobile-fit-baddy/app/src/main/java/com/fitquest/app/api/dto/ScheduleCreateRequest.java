package com.fitquest.app.api.dto;

public class ScheduleCreateRequest {
    public String title;
    public String planned_at;
    public Integer workout_plan_id;
    public String repeat_rule;

    public ScheduleCreateRequest(String title, String plannedAt, Integer workoutPlanId, String repeatRule) {
        this.title = title;
        this.planned_at = plannedAt;
        this.workout_plan_id = workoutPlanId;
        this.repeat_rule = repeatRule;
    }
}
