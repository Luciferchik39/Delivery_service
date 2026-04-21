# apps/delivery/utils.py
from typing import Any

from django.http import HttpRequest


class SessionManager:
    """Утилита для работы с сессиями пользователей"""

    @staticmethod
    def get_session_id(request: HttpRequest) -> str:
        """
        Получить ID сессии текущего пользователя.
        Если сессии нет - создает новую.
        """
        # Проверяем, есть ли session_key
        if not request.session.session_key:
            # Создаем новую сессию
            request.session.create()

        # Явно возвращаем строку (session_key всегда str)
        session_key = request.session.session_key
        return str(session_key) if session_key else ''

    @staticmethod
    def get_or_create_session_id(request: HttpRequest) -> str:
        """Алиас для get_session_id"""
        return SessionManager.get_session_id(request)

    @staticmethod
    def get_session_data(request: HttpRequest) -> dict[str, Any]:
        """Получить все данные сессии"""
        return dict(request.session.items())

    @staticmethod
    def clear_session(request: HttpRequest) -> None:
        """Очистить сессию"""
        request.session.flush()

    @staticmethod
    def set_session_value(request: HttpRequest, key: str, value: Any) -> None:
        """Установить значение в сессии"""
        request.session[key] = value
        request.session.modified = True

    @staticmethod
    def get_session_value(request: HttpRequest, key: str, default: Any = None) -> Any:
        """Получить значение из сессии"""
        return request.session.get(key, default)
