package com.fitquest.app.api.dto;

/** GET /devices: a connected data source of the user (no token). */
public class DeviceInfoDto {
    public String device_id;
    public String name;
    public String kind;
    public String created_at;
    public String last_seen_at;
}
