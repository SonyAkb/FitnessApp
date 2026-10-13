package com.fitquest.app.auth;

/**
 * Client-side checks for the login and register forms.
 * Mirrors the backend rules (RegisterIn in backend-fit-baddy) so the user sees the error before a request.
 */
public final class AuthValidator {

    public static final int MIN_PASSWORD_LENGTH = 8;

    private AuthValidator() {
    }

    /** @return an error message for the form, or {@code null} when the input is valid. */
    public static String validate(String email, String password, String displayName, boolean registerMode) {
        if (isBlank(email) || isBlank(password)) {
            return "Email and password are required";
        }
        if (!email.contains("@") || email.startsWith("@") || email.endsWith("@")) {
            return "Enter a valid email";
        }
        if (!registerMode) {
            return null;
        }
        if (isBlank(displayName)) {
            return "Give yourself a display name";
        }
        return passwordError(password);
    }

    /** @return an error for the password field on registration, or {@code null}. */
    public static String passwordError(String password) {
        if (password == null || password.length() < MIN_PASSWORD_LENGTH) {
            return "Password must be at least " + MIN_PASSWORD_LENGTH + " characters";
        }
        boolean hasLetter = false;
        boolean hasDigit = false;
        for (int i = 0; i < password.length(); i++) {
            char c = password.charAt(i);
            hasLetter |= Character.isLetter(c);
            hasDigit |= Character.isDigit(c);
        }
        if (!hasLetter || !hasDigit) {
            return "Password must contain letters and digits";
        }
        return null;
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
