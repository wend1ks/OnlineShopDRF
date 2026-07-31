from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
    
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import CustomUser, random_code


@dataclass
class ActivationPayload:
    code: str
    attempts: int
    expires_at: timezone.datetime


def _key(user_id: int) -> str:
    return f"activation_code:{user_id}"


def create_activation_for_user(user: CustomUser) -> str:
    """Создаёт (или перезаписывает) код активации в Redis с TTL."""
    ttl = int(getattr(settings, 'ACTIVATION_CODE_TTL', 15 * 60))
    expires_at = timezone.now() + timedelta(seconds=ttl)

    code = random_code()
    cache.set(
        _key(user.id),
        {
            'code': code,
            'attempts': 0,
            'expires_at': expires_at.isoformat(),
        },
        timeout=ttl,
    )
    return code


def get_activation(user: CustomUser) -> ActivationPayload | None:
    data = cache.get(_key(user.id))
    if not data:
        return None
    try:
        expires_at = timezone.datetime.fromisoformat(data['expires_at'])
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at, timezone=timezone.get_current_timezone())
        return ActivationPayload(code=data['code'], attempts=int(data.get('attempts', 0)), expires_at=expires_at)
    except Exception:
        # На случай битых данных — считаем, что кода нет.
        cache.delete(_key(user.id))
        return None


def bump_attempts(user: CustomUser) -> ActivationPayload | None:
    """Инкрементирует attempts и сохраняет оставшийся TTL."""
    payload = get_activation(user)
    if not payload:
        return None
    payload.attempts += 1

    remaining = int((payload.expires_at - timezone.now()).total_seconds())
    if remaining <= 0:
        cache.delete(_key(user.id))
        return None

    cache.set(
        _key(user.id),
        {
            'code': payload.code,
            'attempts': payload.attempts,
            'expires_at': payload.expires_at.isoformat(),
        },
        timeout=remaining,
    )
    return payload


def consume_activation(user: CustomUser) -> None:
    """Удаляет код из Redis (после успешной проверки)."""
    cache.delete(_key(user.id))
