# apps/delivery/views.py
from datetime import datetime

from django.db import connections
from django.db.utils import OperationalError
from loguru import logger
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Parcel, ParcelType
from .serializers import (
    ParcelCreateSerializer,
    ParcelResponseSerializer,
    ParcelTypeSerializer,
)
from .services import currency_service
from .tasks import calculate_all_parcels_delivery_cost, calculate_parcel_delivery_cost
from .utils import SessionManager


class ParcelTypeListAPIView(APIView):
    """API для получения списка типов посылок"""

    def get(self, request: Request) -> Response:
        parcel_types = ParcelType.objects.all()
        serializer = ParcelTypeSerializer(parcel_types, many=True)
        logger.debug(f"Возвращено {parcel_types.count()} типов посылок")
        return Response(serializer.data, status=status.HTTP_200_OK)


class CurrencyRateAPIView(APIView):
    """API для получения текущего курса USD/RUB"""

    def get(self, request: Request) -> Response:
        logger.info("Запрос текущего курса валют")
        rate = currency_service.get_usd_rate()

        if rate is not None:
            logger.success(f"Курс успешно получен: {rate}")
            return Response({
                'rate': rate,
                'currency': 'USD/RUB',
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)

        logger.error("Не удалось получить курс валют")
        return Response({
            'error': 'Не удалось получить курс валюты'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def delete(self, request: Request) -> Response:
        logger.info("Запрос на очистку кеша курса валют")
        success = currency_service.clear_cache()

        if success:
            logger.success("Кеш курса валют очищен")
            return Response({
                'message': 'Кеш курса валют очищен'
            }, status=status.HTTP_200_OK)

        logger.error("Не удалось очистить кеш")
        return Response({
            'error': 'Не удалось очистить кеш'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateParcelAPIView(APIView):
    """API для создания посылки"""

    def post(self, request: Request) -> Response:
        logger.info("Получен запрос на создание посылки")

        session_id = SessionManager.get_session_id(request)
        logger.debug(f"ID сессии: {session_id}")

        serializer = ParcelCreateSerializer(
            data=request.data,
            context={'session_id': session_id}
        )

        if serializer.is_valid():
            parcel = serializer.save()
            logger.success(f"Посылка создана: ID={parcel.id}, Name={parcel.name}")
            return Response({
                'id': parcel.id,
                'message': 'Посылка успешно создана'
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"Ошибки валидации: {serializer.errors}")
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParcelDetailAPIView(APIView):
    """API для получения деталей посылки"""

    def get(self, request: Request, parcel_id: int) -> Response:
        logger.info(f"Запрос деталей посылки ID={parcel_id}")

        session_id = SessionManager.get_session_id(request)

        try:
            parcel = Parcel.objects.get(id=parcel_id, session_id=session_id)
            serializer = ParcelResponseSerializer(parcel)
            logger.debug(f"Детали посылки {parcel_id} отправлены")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parcel.DoesNotExist:
            logger.warning(f"Посылка ID={parcel_id} не найдена в сессии {session_id}")
            return Response({
                'error': 'Посылка не найдена'
            }, status=status.HTTP_404_NOT_FOUND)


class UserParcelsAPIView(APIView):
    """API для получения всех посылок пользователя"""

    def get(self, request: Request) -> Response:
        session_id = SessionManager.get_session_id(request)
        logger.debug(f"Запрос списка посылок для сессии {session_id}")

        parcels = Parcel.objects.filter(session_id=session_id)

        # Пагинация
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        if page_size > 100:
            page_size = 100
        if page_size < 1:
            page_size = 10

        offset = (page - 1) * page_size
        total_count = parcels.count()
        parcels_page = parcels[offset:offset + page_size]

        serializer = ParcelResponseSerializer(parcels_page, many=True)

        logger.info(f"Возвращено {len(parcels_page)} посылок из {total_count} (страница {page}, размер {page_size})")

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 1,
            'results': serializer.data
        }, status=status.HTTP_200_OK)


# apps/delivery/views.py - исправляем сигнатуру метода
class CalculateDeliveryCostAPIView(APIView):
    """API для ручного запуска расчета стоимости доставки"""

    def post(self, request: Request, parcel_id: int | None = None) -> Response:
        """
        POST /api/parcels/calculate/
        POST /api/parcels/<id>/calculate/

        Запускает расчет стоимости доставки.
        """
        if parcel_id is not None:
            # Расчет для конкретной посылки
            logger.info(f"Ручной запуск расчета для посылки {parcel_id}")

            # Проверяем, существует ли посылка и принадлежит ли сессии
            session_id = SessionManager.get_session_id(request)
            try:
                parcel = Parcel.objects.get(id=parcel_id, session_id=session_id)
                logger.debug(f"Посылка найдена: {parcel.name}")
            except Parcel.DoesNotExist:
                logger.warning(f"Посылка {parcel_id} не найдена в сессии {session_id}")
                return Response({
                    'error': 'Посылка не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Запускаем задачу асинхронно
            task = calculate_parcel_delivery_cost.delay(parcel_id)
            logger.success(f"Задача {task.id} запущена для посылки {parcel_id}")

            return Response({
                'message': f'Запущен расчет стоимости для посылки {parcel_id}',
                'task_id': task.id,
                'parcel_id': parcel_id
            }, status=status.HTTP_202_ACCEPTED)
        else:
            # Расчет для всех посылок
            logger.info("Ручной запуск расчета для всех посылок")
            task = calculate_all_parcels_delivery_cost.delay()
            logger.success(f"Задача {task.id} запущена для всех посылок")

            return Response({
                'message': 'Запущен расчет стоимости для всех посылок',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)


class HealthCheckAPIView(APIView):
    """API для проверки здоровья приложения"""

    def get(self, request: Request) -> Response:
        """
        GET /api/health/

        Проверяет:
        - Работоспособность Django
        - Подключение к PostgreSQL
        - Подключение к Redis (опционально)
        - Подключение к Celery (опционально)
        """
        status_data = {
            'status': 'healthy',
            'checks': {}
        }

        # 1. Проверка Django
        status_data['checks']['django'] = 'ok'

        # 2. Проверка PostgreSQL
        try:
            db_conn = connections['default']
            db_conn.cursor()
            status_data['checks']['postgresql'] = 'ok'
        except OperationalError as e:
            status_data['status'] = 'unhealthy'
            status_data['checks']['postgresql'] = 'error'
            logger.error(f"PostgreSQL healthcheck failed: {e}")

        # 3. Проверка Redis
        try:
            from .services import currency_service
            if currency_service.redis_client.ping():
                status_data['checks']['redis'] = 'ok'
            else:
                status_data['checks']['redis'] = 'error'
        except Exception as e:
            status_data['checks']['redis'] = 'error'
            logger.error(f"Redis healthcheck failed: {e}")

        # 4. Проверка Celery (опционально)
        try:
            # Способ 1: Через импорт celery приложения
            from config.celery import app as celery_app
            result = celery_app.control.ping(timeout=2)
            if result:
                status_data['checks']['celery'] = 'ok'
            else:
                status_data['checks']['celery'] = 'error'
        except ImportError:
            # Celery не настроен
            status_data['checks']['celery'] = 'not_configured'
        except Exception as e:
            status_data['checks']['celery'] = 'error'
            logger.error(f"Celery healthcheck failed: {e}")

        # Определяем HTTP статус
        http_status = status.HTTP_200_OK if status_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(status_data, status=http_status)
