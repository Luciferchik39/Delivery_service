# apps/delivery/views.py
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ParcelCreateSerializer, ParcelResponseSerializer
from .utils import SessionManager


class CreateParcelAPIView(APIView):
    """API для создания посылки"""

    def post(self, request: Request) -> Response:
        """POST /api/parcels/create/"""
        # Получаем ID сессии текущего пользователя
        session_id = SessionManager.get_session_id(request)

        # Валидируем данные
        serializer = ParcelCreateSerializer(
            data=request.data,
            context={'session_id': session_id}
        )

        if serializer.is_valid():
            # Сохраняем посылку
            parcel = serializer.save()

            return Response({
                'id': parcel.id,
                'message': 'Посылка успешно создана'
            }, status=status.HTTP_201_CREATED)

        # Возвращаем ошибки валидации
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParcelDetailAPIView(APIView):
    """API для получения деталей посылки"""

    def get(self, request: Request, parcel_id: int) -> Response:
        """GET /api/parcels/{id}/"""
        from .models import Parcel

        session_id = SessionManager.get_session_id(request)

        try:
            parcel = Parcel.objects.get(id=parcel_id, session_id=session_id)
            serializer = ParcelResponseSerializer(parcel)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parcel.DoesNotExist:
            return Response({
                'error': 'Посылка не найдена'
            }, status=status.HTTP_404_NOT_FOUND)


class UserParcelsAPIView(APIView):
    """API для получения всех посылок пользователя"""

    def get(self, request: Request) -> Response:
        """GET /api/parcels/"""
        from .models import Parcel

        session_id = SessionManager.get_session_id(request)
        parcels = Parcel.objects.filter(session_id=session_id)
        serializer = ParcelResponseSerializer(parcels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
