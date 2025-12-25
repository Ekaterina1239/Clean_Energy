from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = [IsAuthenticated]

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


class OccupancyLogViewSet(viewsets.ModelViewSet):
    queryset = OccupancyLog.objects.all()
    serializer_class = OccupancyLogSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        now = timezone.now()
        occupancies = OccupancyLog.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        )
        serializer = self.get_serializer(occupancies, many=True)
        return Response(serializer.data)


class WeatherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherCache.objects.all()
    serializer_class = WeatherCacheSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        weather = WeatherService.get_weather_data()
        serializer = self.get_serializer(weather)
        return Response(serializer.data)


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        recommendations = RecommendationEngine.generate_recommendations()
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
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


class DashboardAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        })