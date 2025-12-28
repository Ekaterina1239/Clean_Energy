# generate_live_data.py
import os
import django
import random
from datetime import datetime, timedelta
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thermasense_project.settings')
django.setup()

from django.utils import timezone
from core.models import Room, EnergyLog, WeatherCache


class LiveDataGenerator:
    """Генератор реалистичных данных в реальном времени"""

    def __init__(self):
        self.rooms = list(Room.objects.all())
        self.base_temp = -5.0

    def simulate_day_night_cycle(self, hour):
        if 0 <= hour < 6:  # Ночь
            return self.base_temp - random.uniform(1, 3)
        elif 6 <= hour < 12:  # Утро
            return self.base_temp + random.uniform(0, 2)
        elif 12 <= hour < 18:  # День
            return self.base_temp + random.uniform(2, 5)
        else:  # Вечер
            return self.base_temp + random.uniform(0, 2)

    def simulate_occupancy_pattern(self, room, hour):
        """Симуляция паттернов занятости"""
        # Офисы: заняты 9-18, конференц-залы: утренние/вечерние встречи
        room_name = room.name.lower()

        if 'office' in room_name or 'it' in room_name or 'hr' in room_name:
            return 9 <= hour < 18
        elif 'conference' in room_name or 'meeting' in room_name or 'board' in room_name:
            return (9 <= hour < 12) or (14 <= hour < 17)
        elif 'training' in room_name or 'class' in room_name:
            return (10 <= hour < 13) or (14 <= hour < 16)
        else:
            return random.random() > 0.7  # 30% chance

    def generate_hourly_data(self):
        """Генерация данных за час"""
        now = timezone.now()
        hour = now.hour

        # Обновляем погоду
        current_temp = self.simulate_day_night_cycle(hour)
        weather_desc = self.get_weather_description(current_temp)

        weather = WeatherCache.objects.create(
            temperature=current_temp,
            humidity=random.randint(65, 85),
            wind_speed=random.uniform(1.5, 5.0),
            description=weather_desc,
            cached_at=now
        )


        for room in self.rooms:
            is_occupied = self.simulate_occupancy_pattern(room, hour)

            if is_occupied and not room.heating_status:
                room.heating_status = True
                room.save()
            elif not is_occupied and room.heating_status:
                if random.random() > 0.3:
                    room.heating_status = False
                    room.save()


            if room.heating_status:
                temp_inside = room.target_temperature
                heating_power = room.area * 0.1 * random.uniform(0.8, 1.2)
            else:
                temp_inside = max(room.comfort_temperature, current_temp + 5)
                heating_power = 0

            EnergyLog.objects.create(
                room=room,
                timestamp=now,
                temperature_inside=temp_inside,
                temperature_outside=current_temp,
                heating_power=heating_power,
                co2_saved=0 if room.heating_status else heating_power * 0.4
            )

        print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Generated data: {current_temp}°C, {len(self.rooms)} rooms")

    def get_weather_description(self, temperature):
        if temperature < -10:
            return "Heavy Snow"
        elif temperature < -5:
            return "Snow"
        elif temperature < 0:
            return "Light Snow"
        elif temperature < 5:
            return "Cloudy"
        else:
            return "Partly Cloudy"

    def run_continuous(self, interval_minutes=5):
        print("🌡️ Starting live data generation...")
        print(f"   Rooms: {len(self.rooms)}")
        print(f"   Interval: {interval_minutes} minutes")
        print("   Press Ctrl+C to stop")
        print("-" * 40)

        try:
            while True:
                self.generate_hourly_data()
                time.sleep(interval_minutes * 60)  # Конвертируем минуты в секунды
        except KeyboardInterrupt:
            print("\n🛑 Live data generation stopped")


if __name__ == '__main__':
    generator = LiveDataGenerator()

    if not generator.rooms:
        print("❌ No rooms found. Please create rooms first.")
        print("Run: python manage.py shell < populate_data.py")
    else:
        generator.generate_hourly_data()
