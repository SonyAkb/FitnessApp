package com.fitquest.app.api;

import com.fitquest.app.api.dto.CompleteSessionRequest;
import com.fitquest.app.api.dto.CreatePlanRequest;
import com.fitquest.app.api.dto.DashboardSummaryDto;
import com.fitquest.app.api.dto.DeviceDto;
import com.fitquest.app.api.dto.DeviceRegisterRequest;
import com.fitquest.app.api.dto.LoginRequest;
import com.fitquest.app.api.dto.NotificationDto;
import com.fitquest.app.api.dto.PetDto;
import com.fitquest.app.api.dto.ProfileUpdateRequest;
import com.fitquest.app.api.dto.RecommendationDto;
import com.fitquest.app.api.dto.RegisterRequest;
import com.fitquest.app.api.dto.ScheduleCreateRequest;
import com.fitquest.app.api.dto.ScheduleItemDto;
import com.fitquest.app.api.dto.SessionCreateRequest;
import com.fitquest.app.api.dto.SessionDto;
import com.fitquest.app.api.dto.SubscriptionDto;
import com.fitquest.app.api.dto.TelemetryDto;
import com.fitquest.app.api.dto.TokenResponse;
import com.fitquest.app.api.dto.UserDto;
import com.fitquest.app.api.dto.WorkoutHistoryDto;
import com.fitquest.app.api.dto.WorkoutPlanDto;

import java.util.List;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.PATCH;
import retrofit2.http.POST;
import retrofit2.http.Path;

/**
 * Shared FitQuest /api/v1 contract (must match backend-fit-baddy).
 */
public interface FitQuestApi {

    @POST("/api/v1/auth/register")
    Call<TokenResponse> register(@Body RegisterRequest body);

    @POST("/api/v1/auth/login")
    Call<TokenResponse> login(@Body LoginRequest body);

    @GET("/api/v1/auth/me")
    Call<UserDto> me();

    @PATCH("/api/v1/profile")
    Call<UserDto> updateProfile(@Body ProfileUpdateRequest body);

    @GET("/api/v1/schedule")
    Call<List<ScheduleItemDto>> getSchedule();

    @POST("/api/v1/schedule")
    Call<ScheduleItemDto> createSchedule(@Body ScheduleCreateRequest body);

    @GET("/api/v1/workouts/plans")
    Call<List<WorkoutPlanDto>> getPlans();

    @POST("/api/v1/workouts/plans")
    Call<WorkoutPlanDto> createPlan(@Body CreatePlanRequest body);

    @POST("/api/v1/workouts/sessions")
    Call<SessionDto> startSession(@Body SessionCreateRequest body);

    @POST("/api/v1/workouts/sessions/{id}/complete")
    Call<SessionDto> completeSession(@Path("id") int id, @Body CompleteSessionRequest body);

    @GET("/api/v1/workouts/history")
    Call<WorkoutHistoryDto> getHistory();

    @GET("/api/v1/pet")
    Call<PetDto> getPet();

    @GET("/api/v1/dashboard/summary")
    Call<DashboardSummaryDto> getDashboard();

    @GET("/api/v1/notifications")
    Call<List<NotificationDto>> getNotifications();

    @POST("/api/v1/notifications/{id}/read")
    Call<NotificationDto> markNotificationRead(@Path("id") int id);

    @POST("/api/v1/devices/register")
    Call<DeviceDto> registerDevice(@Body DeviceRegisterRequest body);

    @GET("/api/v1/telemetry/latest")
    Call<TelemetryDto> getLatestTelemetry();

    @GET("/api/v1/telemetry/history")
    Call<List<TelemetryDto>> getTelemetryHistory();

    @POST("/api/v1/telemetry/simulate")
    Call<TelemetryDto> simulateTelemetry();

    @GET("/api/v1/ai/recommend")
    Call<RecommendationDto> getRecommendation();

    @GET("/api/v1/subscription")
    Call<SubscriptionDto> getSubscription();

    @POST("/api/v1/subscription/checkout")
    Call<SubscriptionDto> checkout();
}
