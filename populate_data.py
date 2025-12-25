# populate_data.py
import os
import django
import random
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thermasense_project.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Building, Room, OccupancyLog, WeatherCache, EnergyLog, Recommendation


def create_demo_data():
    print("🌡️  ThermaSense Demo Data Generator")
    print("=" * 50)

    # Создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username='demo',
        defaults={
            'email': 'demo@thermasense.com',
            'is_staff': True
        }
    )
    if created:
        user.set_password('demo123')
        user.save()

    # Создаем здание
    building, _ = Building.objects.get_or_create(
        name='Tech Campus Building A',
        defaults={
            'address': '123 Innovation Drive, Moscow',
            'total_area': 3500
        }
    )

    # Типичные комнаты для хакатона
    rooms_data = [
        # Конференц-залы
        {'name': 'Main Conference Hall', 'area': 150, 'wall_material': 'concrete', 'target_temp': 22},
        {'name': 'Board Room', 'area': 60, 'wall_material': 'wood', 'target_temp': 23},

        # Офисы
        {'name': 'CEO Office', 'area': 40, 'wall_material': 'wood', 'target_temp': 23},
        {'name': 'IT Department', 'area': 80, 'wall_material': 'panel', 'target_temp': 21},
        {'name': 'HR Office', 'area': 35, 'wall_material': 'brick', 'target_temp': 22},

        # Общие зоны
        {'name': 'Open Space Area', 'area': 200, 'wall_material': 'glass', 'target_temp': 21},
        {'name': 'Kitchen', 'area': 30, 'wall_material': 'concrete', 'target_temp': 20},
        {'name': 'Server Room', 'area': 25, 'wall_material': 'concrete', 'target_temp': 18, 'heating': False},

        # Учебные помещения
        {'name': 'Training Room 1', 'area': 70, 'wall_material': 'brick', 'target_temp': 22},
        {'name': 'Training Room 2', 'area': 65, 'wall_material': 'brick', 'target_temp': 22},
    ]

    print("📊 Creating rooms...")
    rooms = []
    for i, data in enumerate(rooms_data):
        heating = data.get('heating', True)
        room = Room.objects.create(
            building=building,
            name=data['name'],
            area=data['area'],
            wall_material=data['wall_material'],
            heat_loss_coefficient=1.0,
            heating_status=heating and (i % 3 != 0),  # Каждая 3я комната выключена
            target_temperature=data['target_temp'],
            comfort_temperature=18.0
        )
        rooms.append(room)
        print(f"  ✓ {room.name} ({room.area}m²) - Heating: {'ON' if room.heating_status else 'OFF'}")

    # Создаем реальное расписание на сегодня
    print("\n📅 Creating today's schedule...")
    now = timezone.now()
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)

    schedules = [
        # Утренние встречи (9:00-10:30)
        (rooms[0], today_9am, today_9am + timedelta(hours=1.5), "Executive Meeting"),
        (rooms[2], today_9am, today_9am + timedelta(hours=2), "Budget Planning"),

        # Дневные занятия (11:00-13:00)
        (rooms[8], today_9am + timedelta(hours=2), today_9am + timedelta(hours=4), "Python Workshop"),
        (rooms[9], today_9am + timedelta(hours=2.5), today_9am + timedelta(hours=4.5), "Data Science Class"),

        # Текущие занятия (сейчас)
        (rooms[0], now - timedelta(minutes=30), now + timedelta(minutes=60), "Hackathon Presentation"),
        (rooms[3], now - timedelta(minutes=15), now + timedelta(minutes=45), "IT Team Standup"),

        # Вечерние события (15:00-17:00)
        (rooms[1], now + timedelta(hours=1), now + timedelta(hours=3), "Client Meeting"),
    ]

    for room, start, end, purpose in schedules:
        OccupancyLog.objects.create(
            room=room,
            start_time=start,
            end_time=end,
            purpose=purpose,
            is_active=True,
            user=user
        )
        print(f"  ✓ {room.name}: {purpose} ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})")

    # Создаем погодные данные
    print("\n🌤️  Creating weather data...")
    weather = WeatherCache.objects.create(
        temperature=-3.5,
        humidity=72,
        wind_speed=3.8,
        description="Partly Cloudy",
        cached_at=now
    )
    print(f"  ✓ Current weather: {weather.temperature}°C, {weather.description}")

    # Создаем энергетические логи
    print("\n⚡ Creating energy consumption data...")
    for room in rooms:
        for hour in range(24):
            timestamp = now - timedelta(hours=hour)
            heating_power = room.area * 0.1 if room.heating_status else 0

            EnergyLog.objects.create(
                room=room,
                timestamp=timestamp,
                temperature_inside=room.target_temperature if room.heating_status else 18.0,
                temperature_outside=weather.temperature + random.uniform(-2, 2),
                heating_power=heating_power * random.uniform(0.8, 1.2),
                co2_saved=0 if room.heating_status else heating_power * 0.4
            )

    print(f"  ✓ Created 24h energy logs for {len(rooms)} rooms")

    # Создаем умные рекомендации
    print("\n🤖 Creating AI recommendations...")

    # Пример реальных рекомендаций для хакатона
    demo_recommendations = [
        {
            'room': rooms[0],
            'message': "Conference ends in 45 minutes. Thermal analysis shows room will stay warm for 60+ minutes. Turn off heating now to save energy.",
            'action': "Turn off heating immediately",
            'savings': 8.5,
            'priority': 'high'
        },
        {
            'room': rooms[8],
            'message': "No classes scheduled until tomorrow morning. Lower temperature to comfort level (18°C) until 8:00 AM.",
            'action': "Schedule nighttime setback",
            'savings': 12.3,
            'priority': 'medium'
        },
        {
            'room': rooms[3],
            'message': "IT office operates at 40% occupancy but heating runs at 100%. Consider occupancy-based heating control.",
            'action': "Install occupancy sensors",
            'savings': 15.7,
            'priority': 'low'
        },
        {
            'room': rooms[5],
            'message': "Open space area shows high heat loss. Check windows and consider adding thermal curtains.",
            'action': "Improve insulation",
            'savings': 5.2,
            'priority': 'medium'
        }
    ]

    for rec_data in demo_recommendations:
        recommendation = Recommendation.objects.create(
            room=rec_data['room'],
            message=rec_data['message'],
            recommended_action=rec_data['action'],
            estimated_savings=rec_data['savings'],
            priority=rec_data['priority'],
            is_applied=False
        )

        priority_color = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        print(
            f"  {priority_color[rec_data['priority']]} {rec_data['room'].name}: {rec_data['action']} (Save {rec_data['savings']} kWh)")

    # Итоговая статистика
    print("\n" + "=" * 50)
    print("DEMO DATA GENERATION COMPLETE!")
    print("=" * 50)
    print(f"🏢 Buildings: {Building.objects.count()}")
    print(f"🚪 Rooms: {Room.objects.count()}")
    print(f"📅 Active schedules: {OccupancyLog.objects.filter(is_active=True).count()}")
    print(f"🔥 Heating active: {Room.objects.filter(heating_status=True).count()}")
    print(f"⚡ Energy logs: {EnergyLog.objects.count()}")
    print(f"🤖 Recommendations: {Recommendation.objects.count()}")
    print(f"🌡️  Current temperature: {weather.temperature}°C")
    print("\n🔑 Demo credentials:")
    print("   URL: http://localhost:8000/")
    print("   Username: demo")
    print("   Password: demo123")
    print("\n📊 Expected savings from recommendations: 41.7 kWh")
    print("🌍 CO₂ reduction potential: 16.7 kg")
    print("💰 Cost savings: $208.50 (at $5/kWh)")
    print("=" * 50)


if __name__ == '__main__':
    create_demo_data()