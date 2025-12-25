from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rooms', views.RoomViewSet)
router.register(r'occupancies', views.OccupancyLogViewSet)
router.register(r'weather', views.WeatherViewSet, basename='weather')
router.register(r'recommendations', views.RecommendationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.DashboardAPIView.as_view(), name='api_dashboard'),
]