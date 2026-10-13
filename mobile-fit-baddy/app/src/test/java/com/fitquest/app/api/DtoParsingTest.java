package com.fitquest.app.api;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import com.fitquest.app.api.dto.PetDto;
import com.fitquest.app.api.dto.TelemetryDto;
import com.fitquest.app.api.dto.WorkoutHistoryDto;
import com.google.gson.Gson;
import org.junit.Test;

/** Responses from docs/API_CONTRACT.md parse into the client DTOs. */
public class DtoParsingTest {

    private final Gson gson = new Gson();

    @Test
    public void telemetryDtoFromSimulatorAndPiHasSameShape() {
        String sim = "{\"device_id\":\"sim-1\",\"user_id\":12,\"steps\":8432,\"heart_rate\":124,"
                + "\"calories\":420,\"timestamp\":\"2026-10-14T12:00:00Z\",\"source\":\"simulator\"}";
        String pi = sim.replace("sim-1", "pi-1").replace("\"simulator\"", "\"raspberry_pi\"");
        TelemetryDto a = gson.fromJson(sim, TelemetryDto.class);
        TelemetryDto b = gson.fromJson(pi, TelemetryDto.class);
        assertEquals(Integer.valueOf(124), a.heart_rate);
        assertEquals(a.steps, b.steps);
        assertEquals("raspberry_pi", b.source);
    }

    @Test
    public void historyIsAnObjectWithItems() {
        String json = "{\"items\":[{\"id\":1,\"status\":\"completed\",\"plan_name\":\"Legs\"}],\"total\":14}";
        WorkoutHistoryDto history = gson.fromJson(json, WorkoutHistoryDto.class);
        assertEquals(1, history.safeItems().size());
        assertEquals(Integer.valueOf(14), history.total);
    }

    @Test
    public void historyWithoutItemsIsSafe() {
        WorkoutHistoryDto history = gson.fromJson("{\"total\":0}", WorkoutHistoryDto.class);
        assertNotNull(history.safeItems());
        assertTrue(history.safeItems().isEmpty());
    }

    @Test
    public void petDtoParses() {
        String json = "{\"id\":1,\"name\":\"FitBuddy\",\"xp\":80,\"xp_to_next_level\":20,\"level\":1,"
                + "\"energy\":70,\"mood\":\"happy\",\"streak_days\":3}";
        PetDto pet = gson.fromJson(json, PetDto.class);
        assertEquals("happy", pet.mood);
    }
}
