package com.fitquest.app.api.dto;

public class RegisterRequest {
    public String email;
    public String password;
    public String display_name;

    public RegisterRequest(String email, String password, String displayName) {
        this.email = email;
        this.password = password;
        this.display_name = displayName;
    }
}
