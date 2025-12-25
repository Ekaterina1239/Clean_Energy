import math
from datetime import timedelta
from django.utils import timezone
import requests
from django.conf import settings


class ThermalCalculator:
    @staticmethod
    def calculate_cooldown_time(room, current_temp, outside_temp):
        air_heat_capacity = 1005  # J/kg·°C
        air_density = 1.225  # kg/m³
        ceiling_height = 3.0  # m

        volume = room.area * ceiling_height
        air_mass = volume * air_density
        C = air_mass * air_heat_capacity

        U = room.get_heat_loss_factor()
        delta_t = current_temp - room.comfort_temperature
        delta_t_out = current_temp - outside_temp

        if delta_t_out <= 0:
            return float('inf')

        time_seconds = (C * delta_t) / (U * room.area * delta_t_out)
        time_minutes = time_seconds / 60
        time_minutes *= 1.2  # Safety factor

        return max(0, time_minutes)

    @staticmethod
    def calculate_energy_savings(room, hours_saved, outside_temp):
        heating_power_per_sqm = 100  # W/m²
        heating_power = heating_power_per_sqm * room.area / 1000  # kW
        energy_saved = heating_power * hours_saved  # kWh
        co2_saved = energy_saved * 0.4  # kg CO2 (approx for gas)

        return {
            'energy_saved_kwh': energy_saved,
            'co2_saved_kg': co2_saved,
            'money_saved': energy_saved * 5.0,  # Assume 5 currency units per kWh
        }


class WeatherService:
    @staticmethod
    def get_weather_data():
        from .models import WeatherCache

        latest_weather = WeatherCache.objects.first()
        if latest_weather and not latest_weather.is_expired():
            return latest_weather

        try:
            api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
            city = getattr(settings, 'WEATHER_CITY', 'Moscow')

            if api_key:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                response = requests.get(url, timeout=10)
                data = response.json()

                weather = WeatherCache.objects.create(
                    temperature=data['main']['temp'],
                    humidity=data['main']['humidity'],
                    wind_speed=data['wind']['speed'],
                    description=data['weather'][0]['description']
                )
                return weather
            else:
                return WeatherService._get_demo_weather()

        except Exception as e:
            print(f"Weather API error: {e}")
            return WeatherService._get_demo_weather()

    @staticmethod
    def _get_demo_weather():
        from .models import WeatherCache

        weather = WeatherCache.objects.create(
            temperature=-5.0,
            humidity=75,
            wind_speed=3.0,
            description="Cloudy"
        )
        return weather


class RecommendationEngine:
    @staticmethod
    def generate_recommendations():
        from .models import Room, OccupancyLog, Recommendation
        from .utils import WeatherService, ThermalCalculator

        recommendations = []
        weather = WeatherService.get_weather_data()
        rooms = Room.objects.all()

        for room in rooms:
            active_occupancies = room.occupancy_logs.filter(
                is_active=True,
                end_time__gte=timezone.now()
            ).order_by('end_time')

            if not active_occupancies.exists():
                continue

            next_end = active_occupancies.first().end_time
            time_to_end = (next_end - timezone.now()).total_seconds() / 60
            current_temp = room.target_temperature if room.heating_status else room.comfort_temperature

            cooldown_time = ThermalCalculator.calculate_cooldown_time(
                room, current_temp, weather.temperature
            )

            if cooldown_time < time_to_end - 30:  # 30 minutes buffer
                hours_saved = (time_to_end - cooldown_time) / 60
                savings = ThermalCalculator.calculate_energy_savings(
                    room, hours_saved, weather.temperature
                )

                recommendation = Recommendation.objects.create(
                    room=room,
                    message=f"Room {room.name} will be free in {time_to_end:.0f} min. "
                            f"Heat will last for {cooldown_time:.0f} more min.",
                    recommended_action="Turn off heating now",
                    estimated_savings=savings['energy_saved_kwh'],
                    priority='high'
                )
                recommendations.append(recommendation)

        return recommendations