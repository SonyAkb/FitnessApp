package com.fitquest.app.api.dto;

import java.util.ArrayList;
import java.util.List;

public class WorkoutHistoryDto {
    public List<SessionDto> items;
    public Integer total;

    public List<SessionDto> safeItems() {
        return items == null ? new ArrayList<>() : items;
    }
}
