package com.fitquest.app.api.dto;

/** POST /devices/pairing: a 6-digit code the Pi node exchanges for its token. */
public class PairingCodeDto {
    public String code;
    public String kind;
    public String expires_at;
}
