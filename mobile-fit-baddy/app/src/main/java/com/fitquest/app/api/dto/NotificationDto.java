package com.fitquest.app.api.dto;

public class NotificationDto {
    public Integer id;
    public String title;
    public String body;
    public String message;
    public Boolean read;
    public Boolean is_read;
    public String created_at;

    public boolean isRead() {
        return Boolean.TRUE.equals(read) || Boolean.TRUE.equals(is_read);
    }

    public String text() {
        if (body != null && !body.isEmpty()) {
            return body;
        }
        return message == null ? "" : message;
    }
}
