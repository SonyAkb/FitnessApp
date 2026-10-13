package com.fitquest.app.auth;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

import org.junit.Test;

/** US-A1: form checks match the backend rules (AC1.3). */
public class AuthValidatorTest {

    @Test
    public void validRegistrationPasses() {
        assertNull(AuthValidator.validate("anna@example.com", "fit2026go", "Anna", true));
    }

    @Test
    public void emptyEmailOrPasswordIsRejected() {
        assertEquals("Email and password are required", AuthValidator.validate("", "fit2026go", "Anna", true));
        assertEquals("Email and password are required", AuthValidator.validate("a@b.co", " ", "Anna", false));
    }

    @Test
    public void malformedEmailIsRejected() {
        assertEquals("Enter a valid email", AuthValidator.validate("anna.example.com", "fit2026go", "Anna", true));
    }

    @Test
    public void registrationRequiresDisplayName() {
        assertEquals("Give yourself a display name", AuthValidator.validate("a@b.co", "fit2026go", "", true));
    }

    @Test
    public void shortPasswordIsRejectedOnRegistration() {
        assertEquals("Password must be at least 8 characters", AuthValidator.passwordError("fit26"));
    }

    @Test
    public void passwordNeedsLettersAndDigits() {
        assertEquals("Password must contain letters and digits", AuthValidator.passwordError("onlyletters"));
        assertEquals("Password must contain letters and digits", AuthValidator.passwordError("12345678"));
    }

    @Test
    public void loginDoesNotCheckPasswordStrength() {
        assertNull(AuthValidator.validate("a@b.co", "old", null, false));
    }
}
