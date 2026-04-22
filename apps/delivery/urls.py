# apps/delivery/urls.py
from django.urls import path

from .views import (
    CalculateDeliveryCostAPIView,  # ← добавить
    CreateParcelAPIView,
    CurrencyRateAPIView,
    HealthCheckAPIView,
    ParcelDetailAPIView,
    ParcelTypeListAPIView,
    UserParcelsAPIView,
)

app_name = 'delivery'

urlpatterns = [
    # Типы посылок
    path('api/parcel-types/', ParcelTypeListAPIView.as_view(), name='parcel-types'),

    # Курс валют
    path('api/currency-rate/', CurrencyRateAPIView.as_view(), name='currency-rate'),
    path('api/currency-rate/cache/', CurrencyRateAPIView.as_view(), name='currency-rate-cache'),

    # Расчет стоимости
    path('api/parcels/calculate/', CalculateDeliveryCostAPIView.as_view(), name='calculate-all'),
    path('api/parcels/<int:parcel_id>/calculate/', CalculateDeliveryCostAPIView.as_view(), name='calculate-parcel'),

    # Посылки
    path('api/parcels/', UserParcelsAPIView.as_view(), name='parcels-list'),
    path('api/parcels/create/', CreateParcelAPIView.as_view(), name='parcel-create'),
    path('api/parcels/<int:parcel_id>/', ParcelDetailAPIView.as_view(), name='parcel-detail'),

    # Health check
    path('api/health/', HealthCheckAPIView.as_view(), name='health'),
]
