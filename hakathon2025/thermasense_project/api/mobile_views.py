# api/mobile_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone


class MobileDashboardAPI(APIView):
    """API для мобильного приложения"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получение дашборда для мобильного приложения"""
        from core.models import Room, WeatherCache
        from core.utils import WeatherService

        rooms = Room.objects.all()
        weather = WeatherService.get_weather_data()

        # Оптимизированные данные для мобильного приложения
        mobile_data = {
            'user': {
                'username': request.user.username,
                'points': get_user_points(request.user),
                'rank': get_user_rank(request.user)
            },
            'summary': {
                'total_rooms': rooms.count(),
                'occupied_now': get_occupied_rooms_count(),
                'energy_saved_today': get_today_savings(),
                'co2_reduced_today': get_today_co2_reduction()
            },
            'rooms': [
                {
                    'id': room.id,
                    'name': room.name,
                    'status': 'occupied' if is_room_occupied(room) else
                    'heating' if room.heating_status else 'idle',
                    'temperature': room.target_temperature,
                    'heating': room.heating_status,
                    'last_updated': room.updated_at.isoformat()
                }
                for room in rooms
            ],
            'weather': {
                'temperature': weather.temperature,
                'description': weather.description,
                'icon': get_weather_icon(weather.description)
            },
            'notifications': get_unread_notifications(request.user),
            'quick_actions': [
                {'id': 'toggle_all', 'name': 'Toggle All Heating', 'icon': 'power'},
                {'id': 'gen_report', 'name': 'Generate Report', 'icon': 'report'},
                {'id': 'view_analytics', 'name': 'View Analytics', 'icon': 'analytics'}
            ]
        }

        return Response(mobile_data)


class MobilePushNotificationAPI(APIView):
    """API для push-уведомлений"""

    def post(self, request):
        """Отправка push-уведомления"""
        device_token = request.data.get('device_token')
        message = request.data.get('message')
        room_id = request.data.get('room_id')

        # Здесь интеграция с Firebase Cloud Messaging или аналогичным сервисом
        result = send_push_notification(device_token, message)

        return Response({
            'success': result['success'],
            'message_id': result.get('message_id'),
            'timestamp': timezone.now().isoformat()
        })


class VoiceAssistantAPI(APIView):
    """API для голосового помощника (Google Assistant/Alexa)"""

    def post(self, request):
        """Обработка голосовых команд"""
        command = request.data.get('command', '').lower()
        user = request.user

        responses = {
            'turn on heating': handle_heating_command(user, 'on'),
            'turn off heating': handle_heating_command(user, 'off'),
            'what is the temperature': get_temperature_response(),
            'how much energy did i save': get_energy_savings_response(user),
            'give me recommendations': get_recommendations_response(user)
        }

        for key, handler in responses.items():
            if key in command:
                return Response(handler)

        return Response({
            'response': "I'm sorry, I didn't understand that command. "
                        "Try saying 'turn on heating' or 'how much energy did I save?'"
        })