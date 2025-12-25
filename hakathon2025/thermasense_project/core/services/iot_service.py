import asyncio
from django.utils import timezone
import random


class IoTSimulator:
    """Симулятор IoT датчиков для демо"""

    @staticmethod
    def get_sensor_data(room_id):
        """Получение данных с датчиков"""
        # В реальности здесь будет MQTT/WebSocket соединение с датчиками
        return {
            'temperature': round(20 + random.uniform(-2, 5), 1),
            'humidity': random.randint(30, 70),
            'co2_level': random.randint(400, 1200),
            'motion_detected': random.choice([True, False]),
            'people_count': random.randint(0, 10),
            'window_open': random.choice([True, False]),
            'timestamp': timezone.now()
        }

    @staticmethod
    def send_control_command(room_id, command):
        """Отправка команды на IoT устройство"""
        commands = {
            'turn_on_heating': f"Heating ON for room {room_id}",
            'turn_off_heating': f"Heating OFF for room {room_id}",
            'set_temperature': f"Set temperature for room {room_id}",
            'get_status': f"Get status for room {room_id}"
        }

        # Симуляция задержки IoT сети
        import time
        time.sleep(0.5)

        return {
            'success': True,
            'command': commands.get(command, 'Unknown command'),
            'timestamp': timezone.now(),
            'device_id': f"thermostat_{room_id}"
        }


class MQTTHandler:
    """Обработчик MQTT сообщений"""

    def __init__(self):
        self.topics = {
            'temperature': 'thermasense/+/temperature',
            'occupancy': 'thermasense/+/occupancy',
            'energy': 'thermasense/+/energy'
        }

    def subscribe(self):
        """Подписка на топики"""
        # Имитация MQTT подписки
        return True

    def on_message(self, topic, payload):
        """Обработка входящих сообщений"""
        # Здесь будет обработка реальных MQTT сообщений
        return {
            'topic': topic,
            'data': payload,
            'processed_at': timezone.now()
        }