package com.fitquest.app.api.dto;

public class QuestDto {
    public Integer id;
    public String title;        
    public String description;  
    public Integer progress;    
    public Integer target;      
    public String reward;       
    public String status;       
    public String deadline;     

    public int progressClamped() {           
        int p = progress == null ? 0 : Math.max(0, progress);
        int t = target == null || target <= 0 ? 1 : target;
        return Math.min(p, t);
    }
    public int targetSafe() {
        return target == null || target <= 0 ? 1 : target;
    }
    public boolean isCompleted() {
        return "COMPLETED".equalsIgnoreCase(status) || progressClamped() >= targetSafe();
    }
}