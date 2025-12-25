# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class ThermaSenseConsumer(AsyncWebsocketConsumer):
    """WebSocket для real-time обновлений"""

    async def connect(self):
        self.room_group_name = 'thermasense_updates'

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Отправляем начальное состояние
        await self.send_initial_state()

    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Обработка входящих сообщений"""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'toggle_heating':
            await self.handle_toggle_heating(data)
        elif message_type == 'get_room_status':
            await self.send_room_status(data)

    async def send_initial_state(self):
        """Отправка начального состояния"""
        from .models import Room
        from .utils import WeatherService

        rooms = await sync_to_async(list)(Room.objects.all())
        weather = await sync_to_async(WeatherService.get_weather_data)()

        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'rooms': [
                {
                    'id': room.id,
                    'name': room.name,
                    'heating_status': room.heating_status,
                    'temperature': room.target_temperature
                }
                for room in rooms
            ],
            'weather': {
                'temperature': weather.temperature,
                'description': weather.description
            }
        }))

    async def heating_update(self, event):
        """Обработка обновлений отопления"""
        await self.send(text_data=json.dumps({
            'type': 'heating_updated',
            'room_id': event['room_id'],
            'heating_status': event['heating_status'],
            'timestamp': event['timestamp']
        }))

    async def weather_update(self, event):
        """Обработка обновлений погоды"""
        await self.send(text_data=json.dumps({
            'type': 'weather_updated',
            'temperature': event['temperature'],
            'description': event['description'],
            'timestamp': event['timestamp']
        }))

    async def recommendation_alert(self, event):
        """Обработка новых рекомендаций"""
        await self.send(text_data=json.dumps({
            'type': 'new_recommendation',
            'room_name': event['room_name'],
            'message': event['message'],
            'priority': event['priority'],
            'savings': event['savings']
        }))