"""Тесты для логирования подходов и упражнений в сессиях тренировок (WKT-08)."""
import pytest
from tests.conftest import auth_header, create_plan, register_user

SESSIONS = "/api/v1/workouts/sessions"
PLANS = "/api/v1/workouts/plans"


def test_start_session_creates_exercises_and_pending_sets(client):
    """Старт сессии создаёт упражнения и подходы по плану: для sets=3 получаются 3 подхода pending."""
    token, _ = register_user(client)
    headers = auth_header(token)
    
    # Создаем план с конкретным количеством подходов (например, sets=3)
    plan_data = {
        "title": "Workout Plan",
        "exercises": [{"name": "Приседания", "sets": 3, "reps": 10, "weight_kg": 50.0}]
    }
    plan = client.post(PLANS, json=plan_data, headers=headers).json()
    
    # Стартуем сессию
    response = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers)
    assert response.status_code == 201, response.text
    session = response.json()
    
    # Проверяем упражнения и подходы
    assert len(session["exercises"]) == 1
    se = session["exercises"][0]
    assert se["name"] == "Приседания"
    assert len(se["sets"]) == 3
    
    for s in se["sets"]:
        assert s["status"] == "pending"
        assert s["target_reps"] == 10
        assert s["target_weight_kg"] == 50.0
        assert s["actual_reps"] is None
        assert s["actual_weight_kg"] is None


def test_log_set_done_returns_200(client):
    """Отметка done с actual_reps и весом возвращает 200, статус done."""
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    target_set = se["sets"][0]
    
    log_url = f"{SESSIONS}/{session['id']}/sets"
    response = client.post(
        log_url,
        json={
            "session_exercise_id": se["id"],
            "set_index": target_set["set_index"],
            "actual_reps": 12,
            "actual_weight_kg": 60.0,
            "status": "done"
        },
        headers=headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "done"
    assert body["actual_reps"] == 12
    assert body["actual_weight_kg"] == 60.0


def test_log_set_skipped_without_reps(client):
    """Skipped выставляется без actual_reps."""
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    target_set = se["sets"][0]
    
    log_url = f"{SESSIONS}/{session['id']}/sets"
    response = client.post(
        log_url,
        json={
            "session_exercise_id": se["id"],
            "set_index": target_set["set_index"],
            "status": "skipped"
        },
        headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "skipped"
    assert response.json()["actual_reps"] is None


def test_log_set_done_without_reps_gives_422(client):
    """Done без actual_reps даёт 422."""
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    target_set = se["sets"][0]
    
    log_url = f"{SESSIONS}/{session['id']}/sets"
    response = client.post(
        log_url,
        json={
            "session_exercise_id": se["id"],
            "set_index": target_set["set_index"],
            "status": "done",
            "actual_reps": None  # Обязательно для done
        },
        headers=headers
    )
    assert response.status_code == 422


def test_complete_session_calculates_metrics_and_skips_pending(client):
    """Complete переводит неотмеченные подходы в skipped, а в ответе правильные sets_done и volume_kg."""
    token, _ = register_user(client)
    headers = auth_header(token)
    
    # План с одним упражнением у которого 3 подхода
    plan_data = {
        "title": "Volume Test",
        "exercises": [{"name": "Жим", "sets": 3, "reps": 10, "weight_kg": 40.0}]
    }
    plan = client.post(PLANS, json=plan_data, headers=headers).json()
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    
    log_url = f"{SESSIONS}/{session['id']}/sets"
    # Отмечаем только 2 подхода из 3 (по 10 повторов и 40 кг -> volume = 2 * 10 * 40 = 800)
    for i in [1, 2]:
        client.post(
            log_url,
            json={
                "session_exercise_id": se["id"],
                "set_index": i,
                "actual_reps": 10,
                "actual_weight_kg": 40.0,
                "status": "done"
            },
            headers=headers
        )
        
    # Завершаем сессию
    complete_resp = client.post(f"{SESSIONS}/{session['id']}/complete", json={}, headers=headers)
    assert complete_resp.status_code == 200, complete_resp.text
    data = complete_resp.json()
    
    assert data["sets_done"] == 2
    assert data["volume_kg"] == 800.0


def test_cannot_log_set_in_completed_session(client):
    """Отметка в завершённой сессии даёт 409."""
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = create_plan(client, headers)
    
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    
    # Завершаем сессию сразу
    client.post(f"{SESSIONS}/{session['id']}/complete", json={}, headers=headers)
    
    # Пытаемся залогировать подход в завершенную сессию
    log_url = f"{SESSIONS}/{session['id']}/sets"
    response = client.post(
        log_url,
        json={
            "session_exercise_id": se["id"],
            "set_index": 1,
            "actual_reps": 10,
            "actual_weight_kg": 20.0,
            "status": "done"
        },
        headers=headers
    )
    assert response.status_code == 409


def test_foreign_session_or_exercise_gives_404(client):
    """Чужая сессия или чужой session_exercise_id даёт 404."""
    token1, _ = register_user(client, email="user1@example.com")
    headers1 = auth_header(token1)
    plan1 = create_plan(client, headers1)
    session1 = client.post(SESSIONS, json={"plan_id": plan1["id"]}, headers=headers1).json()
    se1 = session1["exercises"][0]
    
    # Другой пользователь
    token2, _ = register_user(client, email="user2@example.com")
    headers2 = auth_header(token2)
    
    log_url_1 = f"{SESSIONS}/{session1['id']}/sets"
    
    # Попытка логировать в чужую сессию
    response_foreign_session = client.post(
        log_url_1,
        json={"session_exercise_id": se1["id"], "set_index": 1, "actual_reps": 10, "status": "done"},
        headers=headers2
    )
    assert response_foreign_session.status_code == 404
    
    # Создаем свою сессию для второго пользователя, но пытаемся передать чужой session_exercise_id
    plan2 = create_plan(client, headers2)
    session2 = client.post(SESSIONS, json={"plan_id": plan2["id"]}, headers=headers2).json()
    
    log_url_2 = f"{SESSIONS}/{session2['id']}/sets"
    response_foreign_exercise = client.post(
        log_url_2,
        json={"session_exercise_id": se1["id"], "set_index": 1, "actual_reps": 10, "status": "done"},
        headers=headers2
    )
    assert response_foreign_exercise.status_code == 404


def test_patch_plan_does_not_affect_active_session(client):
    """После правки плана через PATCH копия в сессии не меняется (история не перезаписывается)."""
    token, _ = register_user(client)
    headers = auth_header(token)
    
    plan = create_plan(client, headers) # Исходное название упражнения из conftest
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    
    original_exercise_name = session["exercises"][0]["name"]
    
    # Меняем план через PATCH
    client.patch(
        f"{PLANS}/{plan['id']}",
        json={"exercises": [{"name": "Совсем другое упражнение", "sets": 2, "reps": 5}]},
        headers=headers
    )
    
    # Проверяем, что в начатой сессии упражнение осталось прежним
    fetched_session = client.get(f"{SESSIONS}/{session['id']}", headers=headers).json()
    assert fetched_session["exercises"][0]["name"] == original_exercise_name


def test_history_sessions_have_sets_done_and_volume_kg(client):
    """В /history у сессий есть sets_done и volume_kg."""
    token, _ = register_user(client)
    headers = auth_header(token)
    
    plan = create_plan(client, headers)
    session = client.post(SESSIONS, json={"plan_id": plan["id"]}, headers=headers).json()
    se = session["exercises"][0]
    
    # Логируем один подход (например, 10 повт, 50 кг)
    client.post(
        f"{SESSIONS}/{session['id']}/sets",
        json={
            "session_exercise_id": se["id"],
            "set_index": 1,
            "actual_reps": 10,
            "actual_weight_kg": 50.0,
            "status": "done"
        },
        headers=headers
    )
    
    # Завершаем тренировку
    client.post(f"{SESSIONS}/{session['id']}/complete", json={}, headers=headers)
    
    # Запрашиваем историю
    history = client.get("/api/v1/workouts/history", headers=headers).json()
    assert history["total"] == 1
    item = history["items"][0]
    
    assert "sets_done" in item
    assert "volume_kg" in item
    assert item["sets_done"] == 1
    assert item["volume_kg"] == 500.0
    # Проверяем также, что в истории список exercises равен None (как требовалось ранее)
    assert item["exercises"] is None