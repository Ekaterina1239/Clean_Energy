import numpy as np
from sklearn.linear_model import LinearRegression
from django.utils import timezone
from datetime import timedelta


class AdvancedThermalCalculator:
    """Улучшенный калькулятор с ML предсказаниями"""

    def __init__(self):
        self.models = {}

    def calculate_dynamic_cooldown(self, room, weather_data, historical_data):
        """
        Динамический расчет с учетом множества факторов
        """
        # Базовые параметры
        base_time = self._calculate_base_cooldown(room, weather_data)

        # Коррекции
        corrections = {
            'window_factor': self._window_correction(room),
            'door_factor': self._door_usage_correction(historical_data),
            'heating_history': self._heating_history_correction(room),
            'sunlight_factor': self._sunlight_correction(room, weather_data),
            'ventilation_factor': self._ventilation_correction(historical_data)
        }

        # Применяем коррекции
        total_correction = 1.0
        for factor in corrections.values():
            total_correction *= factor

        final_time = base_time * total_correction

        # Предсказание с ML
        ml_prediction = self._predict_with_ml(room, weather_data)

        return {
            'cooldown_time': final_time,
            'ml_prediction': ml_prediction,
            'corrections': corrections,
            'confidence': self._calculate_confidence(final_time, ml_prediction)
        }

    def _calculate_base_cooldown(self, room, weather_data):
        """Базовый расчет по улучшенной формуле"""
        # Улучшенная физическая модель
        C_wall = room.area * 0.1 * 1000  # Теплоемкость стен
        C_air = room.area * 3.0 * 1.225 * 1005  # Теплоемкость воздуха
        C_total = C_wall + C_air

        U = room.get_heat_loss_factor()
        delta_T = room.target_temperature - weather_data.temperature
        A = room.area

        # Формула с учетом тепловой инерции
        time_seconds = (C_total * delta_T) / (U * A * max(1, delta_T))

        return time_seconds / 60  # В минутах

    def _predict_with_ml(self, room, weather_data):
        """ML предсказание времени охлаждения"""
        # Здесь будет реальная ML модель
        # Для демо используем линейную регрессию на симулированных данных

        # Симулированные данные для демо
        X = np.array([[room.area, weather_data.temperature,
                       room.get_heat_loss_factor()]])

        # Простая модель (в реальности будет обучена на исторических данных)
        model = LinearRegression()
        model.coef_ = np.array([0.5, -2.3, 15.7])
        model.intercept_ = 30.2

        prediction = model.predict(X)[0]
        return max(0, prediction)

    def _calculate_confidence(self, physics_time, ml_time):
        """Расчет уверенности в предсказании"""
        diff = abs(physics_time - ml_time)
        if diff < 10:
            return 0.95
        elif diff < 30:
            return 0.85
        elif diff < 60:
            return 0.70
        else:
            return 0.50

    def _window_correction(self, room):
        """Коррекция на окна"""
        # В реальности будет учитывать количество и состояние окон
        return 0.8 if hasattr(room, 'has_windows') and room.has_windows else 1.0