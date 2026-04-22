# apps/delivery/exceptions.py
"""
Кастомные исключения и обработчики ошибок для API
"""

from celery.exceptions import CeleryError
from django.conf import settings  # ← добавить импорт
from django.db import DatabaseError
from loguru import logger
from redis.exceptions import RedisError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class DeliveryServiceError(Exception):
    """Базовое исключение для сервиса доставки"""
    pass


class ParcelNotFoundError(DeliveryServiceError):
    """Посылка не найдена"""
    pass


class ParcelValidationError(DeliveryServiceError):
    """Ошибка валидации посылки"""
    pass


class CurrencyRateError(DeliveryServiceError):
    """Ошибка получения курса валют"""
    pass


class SessionError(DeliveryServiceError):
    """Ошибка работы с сессией"""
    pass


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для DRF.
    Логирует все ошибки и возвращает стандартизированный ответ.
    """
    # Получаем стандартный ответ DRF
    response = exception_handler(exc, context)

    # Логируем ошибку
    request = context.get('request')
    view = context.get('view')

    error_context = {
        'exception': exc.__class__.__name__,
        'message': str(exc),
        'view': str(view),
        'path': request.path if request else None,
        'method': request.method if request else None,
    }

    # Обработка различных типов ошибок
    if isinstance(exc, ParcelNotFoundError):
        logger.warning(f"Посылка не найдена: {exc}", extra=error_context)
        return Response(
            {'error': 'Посылка не найдена', 'detail': str(exc)},
            status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, ParcelValidationError):
        logger.warning(f"Ошибка валидации посылки: {exc}", extra=error_context)
        return Response(
            {'error': 'Ошибка валидации', 'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(exc, CurrencyRateError):
        logger.error(f"Ошибка получения курса валют: {exc}", extra=error_context)
        return Response(
            {'error': 'Сервис курсов валют временно недоступен', 'detail': str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if isinstance(exc, SessionError):
        logger.warning(f"Ошибка сессии: {exc}", extra=error_context)
        return Response(
            {'error': 'Ошибка сессии', 'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(exc, DatabaseError):
        logger.critical(f"Ошибка базы данных: {exc}", extra=error_context, exc_info=True)
        return Response(
            {'error': 'Внутренняя ошибка сервера', 'detail': 'Ошибка базы данных'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if isinstance(exc, RedisError):
        logger.error(f"Ошибка Redis: {exc}", extra=error_context)
        # Не возвращаем ошибку клиенту, просто логируем

    if isinstance(exc, CeleryError):
        logger.error(f"Ошибка Celery: {exc}", extra=error_context)

    # Если ответ уже есть (стандартная ошибка DRF)
    if response is not None:
        logger.warning(
            f"DRF ошибка: {response.status_code} - {exc}",
            extra=error_context
        )
        return response

    # Необработанная ошибка
    logger.critical(
        f"Необработанная ошибка: {exc}",
        extra=error_context,
        exc_info=True
    )

    # Используем settings.DEBUG вместо глобальной DEBUG
    return Response(
        {'error': 'Внутренняя ошибка сервера', 'detail': str(exc) if settings.DEBUG else 'Попробуйте позже'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
