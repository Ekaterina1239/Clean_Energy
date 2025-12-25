from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAll
from django.utils import timezone
from core.models import Room, OccupancyLog, WeatherCache, EnergyLog, Recommendation
from .serializers import (
    RoomSerializer, OccupancyLogSerializer, WeatherCacheSerializer,
    EnergyLogSerializer, RecommendationSerializer,
    ThermalAnalysisSerializer, EnergySavingsSerializer
)
from core.utils import WeatherService, ThermalCalculator, RecommendationEngine


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAll]  # Разрешить доступ всем

    @action(detail=True, methods=['post'])
    def toggle_heating(self, request, pk=None):
        room = self.get_object()
        room.heating_status = not room.heating_status
        room.save()

        weather = WeatherService.get_weather_data()
        EnergyLog.objects.create(
            room=room,
            temperature_inside=room.target_temperature if room.heating_status else room.comfort_temperature,
            temperature_outside=weather.temperature,
            heating_power=room.area * 0.1 if room.heating_status else 0,
        )

        return Response({
            'status': 'success',
            'heating_status': room.heating_status,
            'message': f'Heating in {room.name} {"turned on" if room.heating_status else "turned off"}'
        })

    @action(detail=True, methods=['get'])
    def thermal_analysis(self, request, pk=None):
        room = self.get_object()
        weather = WeatherService.get_weather_data()

        current_temp = room.target_temperature if room.heating_status else room.comfort_temperature
        cooldown_time = ThermalCalculator.calculate_cooldown_time(
            room, current_temp, weather.temperature
        )

        recommendation = 'Turn off heating' if cooldown_time > 30 else 'Maintain temperature'

        serializer = ThermalAnalysisSerializer({
            'room_id': room.id,
            'current_temperature': current_temp,
            'outside_temperature': weather.temperature,
            'cooldown_time_minutes': cooldown_time,
            'recommendation': recommendation
        })

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def heated_rooms(self, request):
        """Получить список комнат с включенным отоплением"""
        heated_rooms = self.get_queryset().filter(heating_status=True)
        serializer = self.get_serializer(heated_rooms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unheated_rooms(self, request):
        """Получить список комнат с выключенным отоплением"""
        unheated_rooms = self.get_queryset().filter(heating_status=False)
        serializer = self.get_serializer(unheated_rooms, many=True)
        return Response(serializer.data)


class OccupancyLogViewSet(viewsets.ModelViewSet):
    queryset = OccupancyLog.objects.all()
    serializer_class = OccupancyLogSerializer
    permission_classes = [AllowAll]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущие занятые комнаты"""
        now = timezone.now()
        occupancies = OccupancyLog.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        )
        serializer = self.get_serializer(occupancies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Получить предстоящие занятия"""
        now = timezone.now()
        upcoming_occupancies = OccupancyLog.objects.filter(
            start_time__gt=now,
            is_active=True
        ).order_by('start_time')[:10]
        serializer = self.get_serializer(upcoming_occupancies, many=True)
        return Response(serializer.data)


class WeatherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherCache.objects.all()
    serializer_class = WeatherCacheSerializer
    permission_classes = [AllowAll]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущую погоду"""
        weather = WeatherService.get_weather_data()
        serializer = self.get_serializer(weather)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Получить прогноз погоды (демо-данные)"""
        weather_data = WeatherService.get_weather_data()
        # Демо-прогноз на ближайшие часы
        forecast = {
            'current': {
                'temperature': weather_data.temperature,
                'description': weather_data.description,
                'humidity': weather_data.humidity,
            },
            'next_6_hours': [
                {'hour': 'Now', 'temp': weather_data.temperature},
                {'hour': '+1h', 'temp': weather_data.temperature - 1},
                {'hour': '+2h', 'temp': weather_data.temperature - 2},
                {'hour': '+3h', 'temp': weather_data.temperature - 1},
                {'hour': '+4h', 'temp': weather_data.temperature},
                {'hour': '+5h', 'temp': weather_data.temperature - 1},
            ]
        }
        return Response(forecast)


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [AllowAll]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Сгенерировать новые рекомендации"""
        recommendations = RecommendationEngine.generate_recommendations()
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Применить рекомендацию"""
        recommendation = self.get_object()
        recommendation.is_applied = True
        recommendation.applied_at = timezone.now()
        recommendation.save()

        # Turn off heating for the room
        room = recommendation.room
        room.heating_status = False
        room.save()

        return Response({
            'status': 'success',
            'message': 'Recommendation applied and heating turned off'
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получить активные (не применённые) рекомендации"""
        active_recommendations = self.get_queryset().filter(is_applied=False)
        serializer = self.get_serializer(active_recommendations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def applied(self, request):
        """Получить применённые рекомендации"""
        applied_recommendations = self.get_queryset().filter(is_applied=True)
        serializer = self.get_serializer(applied_recommendations, many=True)
        return Response(serializer.data)


class DashboardAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAll]

    def get(self, request):
        """Получить данные для дашборда"""
        rooms = Room.objects.all()
        weather = WeatherService.get_weather_data()

        total_rooms = rooms.count()
        heated_rooms = rooms.filter(heating_status=True).count()

        occupied_rooms = OccupancyLog.objects.filter(
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now(),
            is_active=True
        ).values('room').distinct().count()

        recommendations = Recommendation.objects.filter(
            is_applied=False
        ).order_by('-priority', '-created_at')[:5]

        total_savings = sum(r.estimated_savings for r in recommendations)

        return Response({
            'total_rooms': total_rooms,
            'heated_rooms': heated_rooms,
            'occupied_rooms': occupied_rooms,
            'weather': {
                'temperature': weather.temperature,
                'description': weather.description,
                'humidity': weather.humidity,
            },
            'recommendations_count': recommendations.count(),
            'total_savings_kwh': total_savings,
            'total_co2_saved_kg': total_savings * 0.4,
            'total_money_saved_rub': total_savings * 5.0,
        })


class EnergyLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EnergyLog.objects.all()
    serializer_class = EnergyLogSerializer
    permission_classes = [AllowAll]

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Потребление энергии за сегодня"""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_logs = self.get_queryset().filter(created_at__gte=today_start)
        total_energy = sum(log.heating_power * 0.01 for log in today_logs)  # Пример расчёта
        return Response({
            'total_energy_kwh': total_energy,
            'logs_count': today_logs.count(),
            'logs': EnergyLogSerializer(today_logs, many=True).data
        })


class StatisticsAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAll]

    def get(self, request):
        """Получить общую статистику"""
        rooms = Room.objects.all()
        total_area = sum(room.area for room in rooms)

        # Расчёт примерной экономии
        heated_area = sum(room.area for room in rooms if room.heating_status)
        potential_savings = (total_area - heated_area) * 0.1 * 8 * 5.0  # руб в день

        return Response({
            'total_rooms': rooms.count(),
            'total_area_m2': total_area,
            'heated_area_m2': heated_area,
            'avg_temperature': sum(r.target_temperature for r in rooms) / rooms.count() if rooms.count() > 0 else 0,
            'daily_potential_savings_rub': potential_savings,
            'daily_co2_savings_kg': potential_savings * 0.08,
            'efficiency_score': min(100, (heated_area / total_area * 100) if total_area > 0 else 0)
        })