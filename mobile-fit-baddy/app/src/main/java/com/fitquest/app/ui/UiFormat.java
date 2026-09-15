package com.fitquest.app.ui;

import com.fitquest.app.R;
import com.fitquest.app.api.dto.DashboardSummaryDto;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

public final class UiFormat {

    private UiFormat() {
    }

    public static int foxForMood(String mood) {
        if (mood == null) {
            return R.drawable.fox_idle;
        }
        switch (mood.toLowerCase()) {
            case "happy":
                return R.drawable.fox_happy;
            case "sad":
                return R.drawable.fox_sad;
            case "level_up":
                return R.drawable.fox_level_up;
            case "neutral":
            case "idle":
            default:
                return R.drawable.fox_idle;
        }
    }

    /**
     * Maps pet moods to animation resources.
     * Add a dedicated animation resource to a mood branch when it is ready.
     */
    public static int foxAnimationForMood(String mood) {
        switch (mood == null ? "" : mood.toLowerCase()) {
            case "happy":
            case "sad":
            case "level_up":
            case "neutral":
            case "idle":
            default:
                return R.drawable.fox_idle_animation;
        }
    }

    public static String moodLine(String mood) {
        if (mood == null) {
            return "Waiting for you";
        }
        switch (mood.toLowerCase()) {
            case "happy":
                return "Fox is buzzing after that session";
            case "sad":
                return "Fox misses the gym";
            case "level_up":
                return "Level up! Fur is glowing";
            case "neutral":
            case "idle":
            default:
                return "Fox is napping until the next quest";
        }
    }

    public static String dash(Integer value) {
        return value == null ? "—" : String.valueOf(value);
    }

    public static String todayTitle(DashboardSummaryDto summary) {
        if (summary == null || summary.today_schedule == null || summary.today_schedule.isJsonNull()) {
            return "No quest on the board yet";
        }
        JsonElement el = summary.today_schedule;
        if (el.isJsonPrimitive()) {
            String text = el.getAsString();
            return text.isEmpty() ? "No quest on the board yet" : text;
        }
        if (el.isJsonObject()) {
            return titleFromObject(el.getAsJsonObject());
        }
        if (el.isJsonArray()) {
            JsonArray array = el.getAsJsonArray();
            if (array.size() == 0) {
                return "No quest on the board yet";
            }
            JsonElement first = array.get(0);
            if (first.isJsonObject()) {
                return titleFromObject(first.getAsJsonObject());
            }
            if (first.isJsonPrimitive()) {
                return first.getAsString();
            }
        }
        return "Today's quest is ready";
    }

    private static String titleFromObject(JsonObject object) {
        if (object.has("title") && !object.get("title").isJsonNull()) {
            return object.get("title").getAsString();
        }
        if (object.has("name") && !object.get("name").isJsonNull()) {
            return object.get("name").getAsString();
        }
        return "Today's quest is ready";
    }
}
