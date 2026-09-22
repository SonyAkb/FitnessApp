package com.fitquest.app.api.dto;

public class CompleteSessionRequest {
    public Integer duration_seconds;

    public CompleteSessionRequest(Integer durationSeconds) {
        this.duration_seconds = durationSeconds;
    }
}
