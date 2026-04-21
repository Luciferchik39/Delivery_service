# apps/delivery/serializers.py
from typing import Any

from rest_framework import serializers

from .models import Parcel, ParcelType


class ParcelTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типа посылки"""

    class Meta:
        model = ParcelType
        fields = ['id', 'name']


class ParcelCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания посылки"""

    # Поле для названия типа (принимаем название, а не ID)
    parcel_type_name = serializers.CharField(write_only=True)

    class Meta:
        model = Parcel
        fields = ['name', 'weight', 'parcel_type_name', 'content_value']

    def validate_name(self, value: str) -> str:
        """Валидация названия"""
        if not value or not value.strip():
            raise serializers.ValidationError("Название посылки не может быть пустым")
        if len(value) > 200:
            raise serializers.ValidationError("Название не может быть длиннее 200 символов")
        return value.strip()

    def validate_weight(self, value: float) -> float:
        """Валидация веса"""
        if value <= 0:
            raise serializers.ValidationError("Вес должен быть больше 0")
        if value > 1000:
            raise serializers.ValidationError("Вес не может превышать 1000 кг")
        return value

    def validate_content_value(self, value: float) -> float:
        """Валидация стоимости содержимого"""
        if value < 0:
            raise serializers.ValidationError("Стоимость не может быть отрицательной")
        if value > 10000000:
            raise serializers.ValidationError("Стоимость не может превышать 10 млн рублей")
        return value

    def validate_parcel_type_name(self, value: str) -> ParcelType:
        """Валидация типа посылки"""
        if not value or not value.strip():
            raise serializers.ValidationError("Тип посылки не может быть пустым")

        # Проверяем, существует ли такой тип
        try:
            parcel_type = ParcelType.objects.get(name=value.strip())
            return parcel_type
        except ParcelType.DoesNotExist as err:
            raise serializers.ValidationError(
                f"Тип посылки '{value}' не найден. Доступные типы: Одежда, Электроника, Разное"
            ) from err

    def create(self, validated_data: dict[str, Any]) -> Parcel:
        """Создание посылки"""
        parcel_type = validated_data.pop('parcel_type_name')
        session_id = self.context.get('session_id')

        parcel = Parcel.objects.create(
            name=validated_data['name'],
            weight=validated_data['weight'],
            parcel_type=parcel_type,
            content_value=validated_data['content_value'],
            session_id=session_id
        )
        return parcel


class ParcelResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа с данными посылки"""

    parcel_type = ParcelTypeSerializer(read_only=True)

    class Meta:
        model = Parcel
        fields = ['id', 'name', 'weight', 'parcel_type', 'content_value',
                  'delivery_cost', 'session_id', 'created_at', 'updated_at']
