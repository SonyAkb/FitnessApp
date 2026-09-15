package com.fitquest.app.api.dto;

public class ExerciseDto {
    public String name;
    public int sets;
    public int reps;
    public Double weight_kg;

    public ExerciseDto() {
    }

    public ExerciseDto(String name, int sets, int reps, Double weightKg) {
        this.name = name;
        this.sets = sets;
        this.reps = reps;
        this.weight_kg = weightKg;
    }

    public String summary() {
        String weight = weight_kg == null ? "" : " @ " + weight_kg + " kg";
        return name + " · " + sets + "×" + reps + weight;
    }
}
