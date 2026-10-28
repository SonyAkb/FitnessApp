"""WKT-06 — каталог упражнений: поиск, фильтр, связь с планом."""
import pytest

from app.modules.workouts import models
from tests.conftest import auth_header, register_user

EXERCISES = "/api/v1/workouts/exercises"
PLANS = "/api/v1/workouts/plans"


@pytest.fixture
def catalog(client, db_session):
    """Создаёт упражнения в тестовой БД (сид из миграции в тестах не применяется)."""
    items = [
        models.Exercise(name="Жим штанги лёжа", muscle_group="chest"),
        models.Exercise(name="Жим стоя", muscle_group="shoulders"),
        models.Exercise(name="Приседания", muscle_group="legs"),
    ]
    db_session.add_all(items)
    db_session.commit()
    return {item.name: item.id for item in items}


def _names(response):
    return [item["name"] for item in response.json()]


def test_list_returns_all_sorted_by_name(client, catalog):
    token, _ = register_user(client)
    response = client.get(EXERCISES, headers=auth_header(token))
    assert response.status_code == 200
    assert _names(response) == ["Жим стоя", "Жим штанги лёжа", "Приседания"]
    assert set(response.json()[0]) == {"id", "name", "muscle_group", "description"}


@pytest.mark.parametrize("q", ["жим", "ЖИМ", "Жим", "  жим  "])
def test_search_is_case_insensitive_for_cyrillic(client, catalog, q):
    token, _ = register_user(client)
    response = client.get(EXERCISES, params={"q": q}, headers=auth_header(token))
    assert response.status_code == 200
    assert _names(response) == ["Жим стоя", "Жим штанги лёжа"]


def test_filter_by_muscle_group(client, catalog):
    token, _ = register_user(client)
    response = client.get(EXERCISES, params={"muscle_group": "chest"}, headers=auth_header(token))
    assert response.status_code == 200
    assert _names(response) == ["Жим штанги лёжа"]


def test_search_and_filter_combined(client, catalog):
    token, _ = register_user(client)
    response = client.get(
        EXERCISES, params={"q": "жим", "muscle_group": "shoulders"}, headers=auth_header(token)
    )
    assert _names(response) == ["Жим стоя"]


def test_search_without_matches_returns_empty_list(client, catalog):
    token, _ = register_user(client)
    response = client.get(EXERCISES, params={"q": "zzz"}, headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == []


def test_unknown_muscle_group_is_rejected(client, catalog):
    token, _ = register_user(client)
    response = client.get(EXERCISES, params={"muscle_group": "wings"}, headers=auth_header(token))
    assert response.status_code == 422


def test_catalog_requires_auth(client):
    assert client.get(EXERCISES).status_code == 401


def test_plan_can_reference_catalog_exercise(client, catalog):
    token, _ = register_user(client)
    headers = auth_header(token)
    exercise_id = catalog["Приседания"]
    response = client.post(
        PLANS,
        json={"title": "Legs", "exercises": [{"name": "Приседания", "exercise_id": exercise_id}]},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["exercises"][0]["exercise_id"] == exercise_id


def test_plan_with_unknown_exercise_id_is_rejected(client, catalog):
    token, _ = register_user(client)
    response = client.post(
        PLANS,
        json={"title": "Bad", "exercises": [{"name": "X", "exercise_id": 99999}]},
        headers=auth_header(token),
    )
    assert response.status_code == 422


def test_plan_with_free_text_exercise_still_works(client):
    token, _ = register_user(client)
    response = client.post(
        PLANS,
        json={"title": "Free", "exercises": [{"name": "Моё упражнение"}]},
        headers=auth_header(token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["exercises"][0]["exercise_id"] is None


def test_patch_plan_validates_exercise_id(client, catalog):
    token, _ = register_user(client)
    headers = auth_header(token)
    plan = client.post(PLANS, json={"title": "P"}, headers=headers).json()

    bad = client.patch(
        f"{PLANS}/{plan['id']}", json={"exercises": [{"name": "X", "exercise_id": 99999}]}, headers=headers
    )
    assert bad.status_code == 422

    ok = client.patch(
        f"{PLANS}/{plan['id']}",
        json={"exercises": [{"name": "Жим стоя", "exercise_id": catalog["Жим стоя"]}]},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["exercises"][0]["exercise_id"] == catalog["Жим стоя"]
