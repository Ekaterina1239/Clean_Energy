from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Room, OccupancyLog
from .utils import WeatherService, ThermalCalculator


@login_required
def room_list(request):
    rooms = Room.objects.all()

    # Calculate statistics
    total_rooms = rooms.count()
    heated_rooms = rooms.filter(heating_status=True).count()
    total_area = sum(room.area for room in rooms)
    avg_temperature = sum(room.target_temperature for room in rooms) / total_rooms if total_rooms > 0 else 0
    total_power = sum(room.area * 0.1 for room in rooms if room.heating_status)

    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'heated_rooms': heated_rooms,
        'total_area': total_area,
        'avg_temperature': avg_temperature,
        'total_power': total_power,
    }

    return render(request, 'core/room_list.html', context)


@login_required
def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    weather = WeatherService.get_weather_data()

    # Calculate thermal analysis
    current_temp = room.target_temperature if room.heating_status else room.comfort_temperature
    cooldown_time = ThermalCalculator.calculate_cooldown_time(room, current_temp, weather.temperature)
    heat_loss_factor = room.get_heat_loss_factor()

    # Get current occupancy
    now = timezone.now()
    current_occupancy = room.occupancy_logs.filter(
        start_time__lte=now,
        end_time__gte=now,
        is_active=True
    ).first()

    # Get upcoming occupancies
    upcoming_occupancies = room.occupancy_logs.filter(
        start_time__gt=now,
        is_active=True
    ).order_by('start_time')[:5]

    # Generate recommendation
    recommendation = None
    if room.heating_status and current_occupancy:
        time_to_end = (current_occupancy.end_time - now).total_seconds() / 60
        if cooldown_time < time_to_end - 30:
            recommendation = f"Turn off heating now. Room will stay warm for {cooldown_time:.0f} more minutes."

    # Sample energy data
    context = {
        'room': room,
        'weather': weather,
        'cooldown_time': cooldown_time,
        'heat_loss_factor': heat_loss_factor,
        'current_occupancy': current_occupancy,
        'upcoming_occupancies': upcoming_occupancies,
        'recommendation': recommendation,
        'today_consumption': room.area * 0.1 * 8 if room.heating_status else 0,
        'weekly_consumption': room.area * 0.1 * 40 if room.heating_status else 0,
        'co2_saved': room.area * 0.1 * 8 * 0.4 if not room.heating_status else 0,
        'cost_today': room.area * 0.1 * 8 * 5.0 if room.heating_status else 0,
        'heating_power': room.area * 0.1,
        'heating_power_percentage': min(room.area * 0.1, 100),
    }

    return render(request, 'core/room_detail.html', context)


@login_required
def toggle_heating(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room.heating_status = not room.heating_status
    room.save()

    return room_detail(request, pk)


@login_required
def generate_recommendations(request):
    from .utils import RecommendationEngine

    recommendations = RecommendationEngine.generate_recommendations()

    context = {
        'recommendations': recommendations,
    }

    return render(request, 'core/recommendations.html', context)