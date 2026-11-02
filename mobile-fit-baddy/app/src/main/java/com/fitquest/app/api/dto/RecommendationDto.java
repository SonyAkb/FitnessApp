package com.fitquest.app.api.dto;

import java.util.List;

public class RecommendationDto {
    public String text;
    public String reason;
    public String intensity;
    public String engine;
    public String disclaimer;
    public List<Source> sources;
    public String created_at;

    public static class Source {
        public String id;
        public String title;
        public String url;
    }
}
