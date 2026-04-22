# apps/delivery/middleware.py
"""
Middleware для логирования HTTP запросов и времени выполнения
"""

import time

from django.utils.deprecation import MiddlewareMixin
from loguru import logger


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware для логирования всех HTTP запросов"""

    def process_request(self, request):
        """Логирование входящего запроса"""
        request.start_time = time.time()

        # Логируем запрос
        logger.debug(
            f"→ {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'user': str(request.user) if request.user.is_authenticated else 'anonymous',
                'session_id': request.session.session_key,
            }
        )

    def process_response(self, request, response):
        """Логирование ответа и времени выполнения"""
        duration = time.time() - request.start_time

        # Определяем уровень логирования по статусу ответа
        log_level = "info"
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"

        # Логируем ответ
        getattr(logger, log_level)(
            f"← {request.method} {request.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'session_id': request.session.session_key,
            }
        )

        return response
