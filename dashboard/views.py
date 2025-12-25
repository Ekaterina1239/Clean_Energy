from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from core.models import Room, OccupancyLog, WeatherCache, Recommendation
from core.utils import WeatherService, RecommendationEngine



def dashboard(request):
    rooms = Room.objects.all()
    weather = WeatherService.get_weather_data()

    # Calculate statistics
    total_rooms = rooms.count()
    heated_rooms = rooms.filter(heating_status=True).count()

    # Calculate occupied rooms
    now = timezone.now()
    occupied_rooms = 0
    for room in rooms:
        if room.occupancy_logs.filter(
                start_time__lte=now,
                end_time__gte=now,
                is_active=True
        ).exists():
            occupied_rooms += 1

    # Generate recommendations
    recommendations = Recommendation.objects.filter(
        is_applied=False
    ).order_by('-priority', '-created_at')[:5]

    # Calculate savings
    total_savings = sum(r.estimated_savings for r in recommendations)
    total_co2_saved = total_savings * 0.4

    context = {
        'total_rooms': total_rooms,
        'heated_rooms': heated_rooms,
        'occupied_rooms': occupied_rooms,
        'weather': weather,
        'recommendations': recommendations,
        'total_savings_kwh': total_savings,
        'total_co2_saved_kg': total_co2_saved,
        'total_money_saved': total_savings * 5.0,
        'rooms': rooms,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def reports(request):
    # Sample data for charts
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    energy_data = [12, 19, 8, 15, 22, 18, 24]
    co2_data = [4.8, 7.6, 3.2, 6.0, 8.8, 7.2, 9.6]

    # Sample top rooms
    top_rooms = [
        {'name': 'Room 101', 'area': 50, 'savings': 45.2, 'percent_saved': 25},
        {'name': 'Conference Hall', 'area': 120, 'savings': 38.7, 'percent_saved': 22},
        {'name': 'Lab 301', 'area': 60, 'savings': 32.5, 'percent_saved': 20},
        {'name': 'Office 205', 'area': 35, 'savings': 28.3, 'percent_saved': 18},
    ]

    context = {
        'labels': labels,
        'energy_data': energy_data,
        'co2_data': co2_data,
        'total_energy': sum(energy_data),
        'total_co2': sum(co2_data),
        'total_cost_savings': sum(energy_data) * 5.0,
        'period_start': (timezone.now() - timedelta(days=7)).date(),
        'period_end': timezone.now().date(),
        'rooms_optimized': len(top_rooms),
        'optimization_rate': 75.5,
        'top_rooms': top_rooms,
        'car_equivalent': sum(co2_data) / 8.9,  # kg CO2 per liter of gasoline
        'tree_equivalent': sum(co2_data) / 21.8,  # kg CO2 absorbed per tree per year
    }

    return render(request, 'dashboard/reports.html', context)



def energy_analytics(request):
    """Расширенная аналитика энергопотребления"""

    # Реальные расчеты вместо демо данных
    rooms = Room.objects.all()
    week_ago = timezone.now() - timedelta(days=7)

    # Собираем реальные данные
    analytics_data = {
        'total_energy_consumed': 0,
        'total_energy_saved': 0,
        'peak_consumption_hours': [],
        'room_efficiency_scores': [],
        'trends': []
    }

    for room in rooms:
        # Расчет потребления
        energy_data = calculate_room_energy(room)
        analytics_data['total_energy_consumed'] += energy_data['consumed']
        analytics_data['total_energy_saved'] += energy_data['saved']

        # Расчет эффективности
        efficiency_score = calculate_efficiency_score(room)
        analytics_data['room_efficiency_scores'].append({
            'room': room.name,
            'score': efficiency_score,
            'savings_potential': calculate_savings_potential(room)
        })

    # Выявление трендов
    analytics_data['trends'] = identify_energy_trends()

    # Рекомендации на основе аналитики
    analytics_data['recommendations'] = generate_analytics_recommendations(analytics_data)

    context = {
        'analytics': analytics_data,
        'period_start': week_ago,
        'period_end': timezone.now(),
        'comparison_period': 'previous week'
    }

    return render(request, 'dashboard/analytics.html', context)


def calculate_room_energy(room):
    """Расчет энергии для комнаты"""
    # Реальные расчеты
    heating_hours = room.occupancy_logs.filter(
        is_active=True,
        end_time__gte=timezone.now() - timedelta(days=7)
    ).aggregate(
        total_hours=Sum(F('end_time') - F('start_time'))
    )['total_hours'] or 0

    # Конвертация в часы
    if isinstance(heating_hours, timedelta):
        heating_hours = heating_hours.total_seconds() / 3600

    # Потребление (кВт·ч)
    power_kw = room.area * 0.1  # 100 Вт/м²
    energy_consumed = power_kw * heating_hours

    # Потенциальная экономия
    # (если бы нагревали по расписанию, а не по occupancy)
    scheduled_hours = 10 * 5  # 10 часов в день, 5 дней
    potential_consumption = power_kw * scheduled_hours
    energy_saved = max(0, potential_consumption - energy_consumed)

    return {
        'consumed': energy_consumed,
        'saved': energy_saved,
        'efficiency': (energy_saved / potential_consumption * 100) if potential_consumption > 0 else 0
    }


def thermal_visualization(request):
    """3D тепловая визуализация здания"""
    rooms = Room.objects.all()

    # Группируем комнаты по этажам
    floors = {}
    for room in rooms:
        # Простая логика: если в названии есть 1xx - первый этаж, 2xx - второй
        floor_num = '1'
        if any(str(i) in room.name for i in ['2', '20', '20']):
            floor_num = '2'
        elif any(str(i) in room.name for i in ['3', '30', '30']):
            floor_num = '3'

        if floor_num not in floors:
            floors[floor_num] = []

        # Определяем статус комнаты
        if room.heating_status and room.target_temperature > 21:
            status = 'hot'
        elif not room.heating_status and room.target_temperature <= 18:
            status = 'cold'
        else:
            status = 'optimal'

        floors[floor_num].append({
            'room': room,
            'status': status,
            'temperature': room.target_temperature if room.heating_status else room.comfort_temperature
        })

    context = {
        'floors': floors,
        'total_rooms': rooms.count(),
        'hot_rooms': rooms.filter(heating_status=True, target_temperature__gt=21).count(),
        'optimal_rooms': rooms.filter(heating_status=True, target_temperature__range=(19, 21)).count(),
        'cold_rooms': rooms.filter(heating_status=False).count(),
    }

    return render(request, 'dashboard/thermal_viz.html', context)



def dashboard(request):
    rooms = Room.objects.all()
    weather = WeatherService.get_weather_data()

    # Gamification data
    leaders = [
        {'name': 'Physics Department', 'points': 2540, 'savings': 45.2, 'description': 'Best optimization rate'},
        {'name': 'Computer Science', 'points': 1980, 'savings': 38.7, 'description': 'Most consistent savings'},
        {'name': 'Mathematics', 'points': 1750, 'savings': 32.5, 'description': 'Perfect schedule adherence'},
        {'name': 'Chemistry', 'points': 1420, 'savings': 28.3, 'description': 'Great weekend optimization'},
        {'name': 'Biology', 'points': 1150, 'savings': 22.1, 'description': 'Improving rapidly'},
    ]

    # Calculate user points (simulated for demo)
    import random
    user_points = random.randint(800, 1500)
    user_level = min(5, user_points // 300 + 1)

    # Calculate statistics
    total_rooms = rooms.count()
    heated_rooms = rooms.filter(heating_status=True).count()

    # Calculate occupied rooms
    now = timezone.now()
    occupied_rooms = 0
    for room in rooms:
        if room.occupancy_logs.filter(
                start_time__lte=now,
                end_time__gte=now,
                is_active=True
        ).exists():
            occupied_rooms += 1

    # Generate recommendations
    from core.utils import RecommendationEngine
    recommendations = RecommendationEngine.generate_recommendations()

    # Calculate savings
    total_savings = sum(r.estimated_savings for r in recommendations[:5])
    total_co2_saved = total_savings * 0.4

    context = {
        'total_rooms': total_rooms,
        'heated_rooms': heated_rooms,
        'occupied_rooms': occupied_rooms,
        'weather': weather,
        'recommendations': list(recommendations)[:5],
        'total_savings_kwh': total_savings,
        'total_co2_saved_kg': total_co2_saved,
        'total_money_saved': total_savings * 5.0,
        'rooms': rooms,
        'leaders': leaders,  # NEW
        'user_points': user_points,  # NEW
        'user_level': user_level,  # NEW
        'next_level_points': user_level * 300,  # NEW
    }

    return render(request, 'dashboard/dashboard.html', context)