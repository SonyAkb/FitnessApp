package com.fitquest.app.api.dto;

public class AchievementDto {
    public Integer id;
    public String title;         
    public String description;   
    public String earned_at;   
    public Integer xp_reward;  
    public String code;

    public String dateText() {   
        if (earned_at == null || earned_at.isEmpty()) return "";
        try {
            java.time.LocalDate d = java.time.LocalDate.parse(earned_at.substring(0, 10));
            return d.toString(); 
        } catch (Exception e) {
            return earned_at;
        }
    }
}