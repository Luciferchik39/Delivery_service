# apps/delivery/urls.py
from django.urls import path

from .views import CreateParcelAPIView, ParcelDetailAPIView, UserParcelsAPIView

app_name = 'delivery'

urlpatterns = [
    path('api/parcels/', UserParcelsAPIView.as_view(), name='parcels-list'),
    path('api/parcels/create/', CreateParcelAPIView.as_view(), name='parcel-create'),
    path('api/parcels/<int:parcel_id>/', ParcelDetailAPIView.as_view(), name='parcel-detail'),
]
