package com.fitquest.app.api.dto;

import com.google.gson.JsonElement;

public class DashboardSummaryDto {
    public Integer completed_workouts_count;
    public Integer current_streak_days;
    public Integer xp;
    public Integer level;
    public String mood;
    public Integer last_heart_rate;
    public Integer last_steps;
    public JsonElement today_schedule;
}
