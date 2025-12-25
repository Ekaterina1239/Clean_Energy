from rest_framework import serializers
from core.models import Room, OccupancyLog, WeatherCache, EnergyLog, Recommendation


class RoomSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    heat_loss_factor = serializers.SerializerMethodField()
    current_status = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_heat_loss_factor(self, obj):
        return obj.get_heat_loss_factor()

    def get_current_status(self, obj):
        from django.utils import timezone

        occupancy = obj.occupancy_logs.filter(
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now(),
            is_active=True
        ).first()

        if occupancy:
            return 'occupied'
        elif obj.heating_status:
            return 'heating'
        else:
            return 'idle'


class OccupancyLogSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = OccupancyLog
        fields = '__all__'

    def get_duration_minutes(self, obj):
        return obj.duration_minutes()


class WeatherCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherCache
        fields = '__all__'


class EnergyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyLog
        fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = Recommendation
        fields = '__all__'


class ThermalAnalysisSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    current_temperature = serializers.FloatField()
    outside_temperature = serializers.FloatField()
    cooldown_time_minutes = serializers.FloatField()
    recommendation = serializers.CharField()


class EnergySavingsSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    energy_saved_kwh = serializers.FloatField()
    co2_saved_kg = serializers.FloatField()
    money_saved = serializers.FloatField()