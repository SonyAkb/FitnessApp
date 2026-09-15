from pydantic import BaseModel

from app.modules.auth.schemas import ScheduleOut


class WorkoutByDay(BaseModel):
    date: str
    completed: int


class DashboardSummaryOut(BaseModel):
    completed_workouts_count: int
    current_streak_days: int
    xp: int
    level: int
    mood: str
    last_heart_rate: int | None
    last_steps: int | None
    today_schedule: list[ScheduleOut]
    period: str = "week"
    total_workouts: int = 0
    completed_workouts: int = 0
    missed_workouts: int = 0
    companion_mood: str = "neutral"
    steps_7d: int | None = None
    workouts_by_day: list[WorkoutByDay] = []
