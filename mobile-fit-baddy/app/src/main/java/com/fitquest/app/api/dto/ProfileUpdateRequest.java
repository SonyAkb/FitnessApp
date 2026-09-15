package com.fitquest.app.api.dto;

public class ProfileUpdateRequest {
    public String display_name;
    public String goal;
    public Double weight_kg;
    public String fitness_level;

    public ProfileUpdateRequest(String displayName, String goal, Double weightKg, String fitnessLevel) {
        this.display_name = emptyToNull(displayName);
        this.goal = emptyToNull(goal);
        this.weight_kg = weightKg;
        this.fitness_level = emptyToNull(fitnessLevel);
    }

    private static String emptyToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
