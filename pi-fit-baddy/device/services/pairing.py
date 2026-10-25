"""Сопряжение узла с backend по коду из приложения.

Пользователь в приложении нажимает «Подключить Raspberry Pi» и получает 6-значный код
(живёт 10 минут). Узел запускается с `PAIRING_CODE=<код>`, сам обменивает его на свой
`device_token` (`POST /api/v1/devices/pair`) и сохраняет токен в `DEVICE_TOKEN_FILE`.
Следующие запуски берут токен из файла — код больше не нужен. Телефон и узел друг о друге
не знают: оба работают только с backend.

Порядок выбора учётных данных: `DEVICE_TOKEN` из окружения → новый `PAIRING_CODE` →
сохранённый файл (если он для того же backend и устройства).
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
from dataclasses import dataclass

import httpx

from device.config import Config

PAIR_PATH = "/api/v1/devices/pair"

logger = logging.getLogger(__name__)


class PairingError(ValueError):
    """Не удалось получить токен устройства; запуск публикации невозможен."""


@dataclass(frozen=True)
class Credentials:
    device_id: str
    device_token: str


def default_device_id() -> str:
    """`pi-<hostname>`: стабильно между перезапусками и понятно в списке устройств приложения."""
    host = re.sub(r"[^a-z0-9-]+", "-", socket.gethostname().lower()).strip("-") or "node"
    return f"pi-{host}"[:80]


def load_saved(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        logger.warning("Файл токена %s не читается — нужен новый PAIRING_CODE", path)
        return None
    if not isinstance(data, dict) or not data.get("device_token") or not data.get("device_id"):
        return None
    return data


def save(path: str, *, backend_url: str, credentials: Credentials) -> None:
    """Атомарная запись с правами 600: токен — секрет устройства."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = f"{path}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"backend_url": backend_url, "device_id": credentials.device_id,
                   "device_token": credentials.device_token}, fh)
    os.replace(tmp, path)


async def pair(client: httpx.AsyncClient, backend_url: str, code: str, device_id: str) -> str:
    url = backend_url.rstrip("/") + PAIR_PATH
    try:
        response = await client.post(url, json={"code": code, "device_id": device_id})
    except httpx.HTTPError as exc:
        raise PairingError(f"Backend недоступен для сопряжения ({type(exc).__name__}): проверьте BACKEND_URL") from exc
    if response.status_code == 200:
        token = response.json().get("device_token")
        if token:
            return token
    if response.status_code == 404:
        raise PairingError("Код сопряжения неверный или истёк — получите новый в приложении")
    if response.status_code == 409:
        raise PairingError(f"Устройство {device_id} уже привязано к другому пользователю — задайте другой DEVICE_ID")
    if response.status_code == 422:
        raise PairingError("Код сопряжения — 6 цифр из приложения")
    raise PairingError(f"Сопряжение не удалось: backend ответил {response.status_code}")


async def resolve_credentials(config: Config, client: httpx.AsyncClient) -> Credentials | None:
    """Учётные данные для публикатора; None — пусть Publisher сам сообщит, чего не хватает."""
    if config.device_token:
        return None  # явно заданный токен: старый путь, ничего не меняем
    backend_url = (config.backend_url or "").strip()
    saved = load_saved(config.device_token_file)
    if config.pairing_code:
        if not backend_url:
            return None
        device_id = config.device_id or (saved or {}).get("device_id") or default_device_id()
        token = await pair(client, backend_url, config.pairing_code.strip(), device_id)
        credentials = Credentials(device_id=device_id, device_token=token)
        save(config.device_token_file, backend_url=backend_url, credentials=credentials)
        logger.info("Узел %s сопряжён с %s; токен сохранён в %s", device_id, backend_url, config.device_token_file)
        return credentials
    if saved and saved.get("backend_url") == backend_url and (not config.device_id or config.device_id == saved["device_id"]):
        return Credentials(device_id=saved["device_id"], device_token=saved["device_token"])
    return None
