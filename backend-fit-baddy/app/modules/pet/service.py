from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.events import ACHIEVEMENT_EARNED, PET_LEVELED_UP, QUEST_COMPLETED, event_bus
from app.modules.pet import models

XP_PER_WORKOUT = 25
XP_PER_LEVEL = 100
ENERGY_GAIN = 15
ENERGY_LOSS = 20
ENERGY_MIN = 0
ENERGY_MAX = 100

QUEST_CATALOG = [
    {"code": "one_workout_today", "title": "1 тренировка сегодня",
     "period": "daily", "target": 1, "xp_reward": 20},
    {"code": "three_workouts_week", "title": "3 тренировки за неделю",
     "period": "weekly", "target": 3, "xp_reward": 50},
]

ACHIEVEMENT_CATALOG = [
    {"code": "first_workout", "title": "Первая тренировка", "xp_reward": 10},
    {"code": "three_in_row", "title": "3 тренировки подряд", "xp_reward": 30},
    {"code": "week_no_miss", "title": "Неделя без пропусков", "xp_reward": 40},
]


def get_pet(db: Session, user_id: int) -> models.Pet | None:
    return db.query(models.Pet).filter(models.Pet.user_id == user_id).first()


def get_or_create_pet(db: Session, user_id: int, name: str = "FitBuddy") -> models.Pet:
    pet = get_pet(db, user_id)
    if pet is None:
        pet = models.Pet(user_id=user_id, name=name)
        db.add(pet)
        db.flush()
    return pet

def ensure_catalog(db: Session) -> None:
    known = {code for (code,) in db.query(models.Quest.code).all()}
    for item in QUEST_CATALOG:
        if item["code"] not in known:
            db.add(models.Quest(**item))
    known = {code for (code,) in db.query(models.Achievement.code).all()}
    for item in ACHIEVEMENT_CATALOG:
        if item["code"] not in known:
            db.add(models.Achievement(**item))
    db.flush()


def deadline_for(period_start_at: datetime | None, period: str) -> datetime | None:
    if period_start_at is None:
        return None
    span = timedelta(days=7) if period == "weekly" else timedelta(days=1)
    return period_start_at + span


def ensure_user_quests(db: Session, user_id: int) -> list[models.UserQuest]:
    ensure_catalog(db)
    existing = {uq.quest_id for uq in db.query(models.UserQuest).filter(
        models.UserQuest.user_id == user_id).all()}
    for quest in db.query(models.Quest).order_by(models.Quest.id).all():
        if quest.id not in existing:
            db.add(models.UserQuest(
                user_id=user_id,
                quest_id=quest.id,
                progress=0,
                period_start=period_start(utc_now(), quest.period),
                notified=False,
            ))
    db.flush()
    return db.query(models.UserQuest).filter(models.UserQuest.user_id == user_id).all()


def award_xp(db: Session, pet: models.Pet, amount: int) -> models.Pet:
    old_level = pet.level
    pet.xp += amount
    pet.level = pet.xp // XP_PER_LEVEL + 1
    pet.updated_at = utc_now()
    if pet.level > old_level:
        pet.mood = "level_up"
        event_bus.publish(
            PET_LEVELED_UP,
            {"user_id": pet.user_id, "level": pet.level, "name": pet.name},
            db,
        )
    db.flush()
    return pet

def apply_workout_completed(db: Session, user_id: int, completed_at) -> models.Pet:
    pet = get_or_create_pet(db, user_id)
    old_level = pet.level
    pet.xp += XP_PER_WORKOUT
    pet.level = pet.xp // XP_PER_LEVEL + 1
    pet.energy = min(ENERGY_MAX, pet.energy + ENERGY_GAIN)
    pet.updated_at = utc_now()

    when = completed_at.date() if hasattr(completed_at, "date") else utc_now().date()
    if pet.last_activity_date == when:
        pass
    elif pet.last_activity_date and pet.last_activity_date == when - timedelta(days=1):
        pet.streak_days += 1
    else:
        pet.streak_days = 1
    pet.last_activity_date = when

    if pet.level > old_level:
        pet.mood = "level_up"
        event_bus.publish(
            PET_LEVELED_UP,
            {"user_id": user_id, "level": pet.level, "name": pet.name},
            db,
        )
    else:
        pet.mood = "happy"
    db.flush()
    return pet

def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def period_start(when: datetime, period: str) -> datetime:
    day = when.date() if isinstance(when, datetime) else when
    if period == "weekly":
        start = day - timedelta(days=day.weekday())
    else:
        start = day
    return datetime(start.year, start.month, start.day, tzinfo=timezone.utc)


def _reset_if_new_period(uq: models.UserQuest, quest: models.Quest, now: datetime) -> None:
    start = period_start(now, quest.period)
    stored = _as_utc(uq.period_start) if uq.period_start is not None else None
    if stored is None or stored != start:
        uq.period_start = start
        uq.progress = 0
        uq.completed_at = None
        uq.notified = False


def apply_quest_progress(db: Session, user_id: int, when: datetime) -> list[models.Quest]:
    now = _as_utc(when) if isinstance(when, datetime) else utc_now()
    ensure_user_quests(db, user_id)
    pet = get_or_create_pet(db, user_id)
    rows = (
        db.query(models.UserQuest, models.Quest)
        .join(models.Quest, models.Quest.id == models.UserQuest.quest_id)
        .filter(models.UserQuest.user_id == user_id)
        .order_by(models.Quest.id)
        .all()
    )
    finished: list[models.Quest] = []
    for uq, quest in rows:
        _reset_if_new_period(uq, quest, now)
        if uq.completed_at is not None:
            continue
        uq.progress = min(quest.target, uq.progress + 1)
        if uq.progress >= quest.target:
            uq.completed_at = now
            award_xp(db, pet, quest.xp_reward)
            
            uq.notified = True
            finished.append(quest)
            event_bus.publish(
                QUEST_COMPLETED,
                {
                    "user_id": user_id,
                    "code": quest.code,
                    "title": quest.title,
                    "xp_reward": quest.xp_reward,
                },
                db,
            )
    db.flush()
    return finished


def _earn_achievement(db: Session, user_id: int, code: str, now: datetime) -> models.Achievement | None:
    ach = db.query(models.Achievement).filter(models.Achievement.code == code).first()
    if ach is None:
        return None
    already = (
        db.query(models.UserAchievement)
        .filter(
            models.UserAchievement.user_id == user_id,
            models.UserAchievement.achievement_id == ach.id,
        )
        .first()
    )
    if already is not None:
        return None
    db.add(models.UserAchievement(user_id=user_id, achievement_id=ach.id, earned_at=now))
    db.flush()
    pet = get_or_create_pet(db, user_id)
    award_xp(db, pet, ach.xp_reward)
    event_bus.publish(
        ACHIEVEMENT_EARNED,
        {"user_id": user_id, "code": ach.code, "title": ach.title, "xp_reward": ach.xp_reward},
        db,
    )
    return ach


def evaluate_achievements(db: Session, user_id: int, when: datetime | None = None) -> list[models.Achievement]:
    now = when if isinstance(when, datetime) else utc_now()
    ensure_catalog(db)
    pet = get_or_create_pet(db, user_id)
    earned: list[models.Achievement] = []
    if pet.last_activity_date is not None:
        result = _earn_achievement(db, user_id, "first_workout", now)
        if result:
            earned.append(result)
    if pet.streak_days >= 3:
        result = _earn_achievement(db, user_id, "three_in_row", now)
        if result:
            earned.append(result)
    if pet.streak_days >= 7:
        result = _earn_achievement(db, user_id, "week_no_miss", now)
        if result:
            earned.append(result)
    return earned


def list_user_quests(db: Session, user_id: int) -> list[tuple[models.UserQuest, models.Quest]]:
    ensure_user_quests(db, user_id)
    return (
        db.query(models.UserQuest, models.Quest)
        .join(models.Quest, models.Quest.id == models.UserQuest.quest_id)
        .filter(models.UserQuest.user_id == user_id)
        .order_by(models.Quest.id)
        .all()
    )


def list_user_achievements(db: Session, user_id: int) -> list[tuple[models.UserAchievement, models.Achievement]]:
    ensure_catalog(db)
    return (
        db.query(models.UserAchievement, models.Achievement)
        .join(models.Achievement, models.Achievement.id == models.UserAchievement.achievement_id)
        .filter(models.UserAchievement.user_id == user_id)
        .order_by(models.UserAchievement.earned_at.desc(), models.UserAchievement.id.desc())
        .all()
    )

def apply_workout_missed(db: Session, user_id: int) -> models.Pet:
    pet = get_or_create_pet(db, user_id)
    pet.energy = max(ENERGY_MIN, pet.energy - ENERGY_LOSS)
    pet.mood = "sad"
    pet.streak_days = 0
    pet.updated_at = utc_now()
    db.flush()
    return pet


def pet_out(pet: models.Pet):
    from app.modules.pet.schemas import PetOut

    remaining = XP_PER_LEVEL - (pet.xp % XP_PER_LEVEL)
    if remaining == 0:
        remaining = XP_PER_LEVEL
    return PetOut(
        id=pet.id,
        name=pet.name,
        xp=pet.xp,
        xp_to_next_level=remaining,
        level=pet.level,
        energy=pet.energy,
        mood=pet.mood,
        streak_days=pet.streak_days,
        updated_at=pet.updated_at,
    )

def quest_out(row: tuple[models.UserQuest, models.Quest]):
    from app.modules.pet.schemas import QuestOut

    uq, quest = row
    status = "completed" if uq.completed_at is not None else "in_progress"
    return QuestOut(
        id=quest.id,
        code=quest.code,
        title=quest.title,
        description=f"{quest.title}: {quest.target} шт. за период '{quest.period}'.",
        period=quest.period,
        progress=uq.progress,
        target=quest.target,
        xp_reward=quest.xp_reward,
        status=status,
        deadline=deadline_for(uq.period_start, quest.period),
        completed_at=uq.completed_at,
    )


def achievement_out(row: tuple[models.UserAchievement, models.Achievement]):
    from app.modules.pet.schemas import AchievementOut

    ua, ach = row
    return AchievementOut(
        id=ach.id,
        code=ach.code,
        title=ach.title,
        description=ach.title,
        xp_reward=ach.xp_reward,
        earned_at=ua.earned_at,
    )