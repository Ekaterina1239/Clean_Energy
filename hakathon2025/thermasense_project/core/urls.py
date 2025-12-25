from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/toggle/', views.toggle_heating, name='toggle_heating'),
    path('recommendations/', views.generate_recommendations, name='generate_recommendations'),
]