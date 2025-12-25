# core/services/chatbot_service.py
import openai
from django.conf import settings


class ThermaSenseChatbot:
    """AI чатбот для энергетических рекомендаций"""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.context = """
        You are ThermaSense AI Assistant, an expert in energy efficiency and heating optimization.
        You help users save energy and reduce costs in buildings.
        Provide specific, actionable recommendations based on building data.
        """

    def get_recommendation(self, user_query, building_data):
        """Получение рекомендаций от AI"""

        if not self.api_key:
            # Демо режим без OpenAI API
            return self._get_demo_recommendation(user_query)

        try:
            # Используем OpenAI API
            openai.api_key = self.api_key

            prompt = f"""
            Context: {self.context}

            Building Data:
            - Total rooms: {building_data.get('total_rooms', 0)}
            - Heated rooms: {building_data.get('heated_rooms', 0)}
            - Outside temperature: {building_data.get('outside_temp', 0)}°C
            - Current energy consumption: {building_data.get('energy_consumption', 0)} kWh

            User Question: {user_query}

            Please provide specific, actionable recommendations to save energy:
            1. Immediate actions (can be done today)
            2. Medium-term optimizations (next week)
            3. Long-term investments
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.context},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"AI recommendation service is temporarily unavailable. {str(e)}"

    def _get_demo_recommendation(self, user_query):
        """Демо рекомендации без API"""

        recommendations = {
            "how to save energy": """
            Based on your building data, here are specific recommendations:

            1. **Immediate Actions (Today):**
               - Turn off heating in Room 101 (empty since 2 PM)
               - Lower corridor temperature from 22°C to 18°C
               - Schedule heating 30 minutes before occupancy instead of 1 hour

            2. **This Week:**
               - Install occupancy sensors in 3 high-traffic rooms
               - Review and optimize heating schedules
               - Educate staff about energy-saving practices

            3. **Long Term:**
               - Consider smart thermostats for all rooms
               - Improve insulation in north-facing rooms
               - Install solar panels for partial self-sufficiency
            """,

            "heating optimization": """
            Heating Optimization Recommendations:

            **Smart Scheduling:**
            - Use thermal inertia: Turn off heating 45 min before room vacates
            - Implement zone-based heating control
            - Integrate with Google Calendar for automatic scheduling

            **Technical Improvements:**
            - Balance heating system for even temperature distribution
            - Regular maintenance of radiators and pipes
            - Install programmable thermostats with learning capabilities

            **Expected Savings:** 25-40% reduction in heating costs
            """
        }

        # Находим наиболее релевантную рекомендацию
        for key in recommendations:
            if key in user_query.lower():
                return recommendations[key]

        return recommendations["how to save energy"]