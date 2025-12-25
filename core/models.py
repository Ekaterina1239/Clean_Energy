from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User


class Building(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    total_area = models.FloatField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Building"
        verbose_name_plural = "Buildings"


class Room(models.Model):
    WALL_MATERIAL_CHOICES = [
        ('brick', 'Brick'),
        ('concrete', 'Concrete'),
        ('wood', 'Wood'),
        ('panel', 'Panel'),
        ('monolithic', 'Monolithic'),
    ]

    name = models.CharField(max_length=200)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    area = models.FloatField(validators=[MinValueValidator(1)])
    wall_material = models.CharField(max_length=20, choices=WALL_MATERIAL_CHOICES)
    heat_loss_coefficient = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)]
    )
    heating_status = models.BooleanField(default=False)
    target_temperature = models.FloatField(default=22.0)
    comfort_temperature = models.FloatField(default=18.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.building.name})"

    def get_heat_loss_factor(self):
        factors = {
            'brick': 1.2,
            'concrete': 1.5,
            'wood': 0.8,
            'panel': 1.8,
            'monolithic': 1.3,
        }
        return factors.get(self.wall_material, 1.0) * self.heat_loss_coefficient

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"


class OccupancyLog(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='occupancy_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    purpose = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.name}: {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def duration_minutes(self):
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() / 60
        return 0

    @property
    def is_currently_occupied(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active

    class Meta:
        verbose_name = "Occupancy Log"
        verbose_name_plural = "Occupancy Logs"
        ordering = ['-start_time']


class WeatherCache(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=200)
    cached_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.temperature}°C at {self.cached_at}"

    def is_expired(self):
        return (timezone.now() - self.cached_at).total_seconds() > 10800

    class Meta:
        verbose_name = "Weather Cache"
        verbose_name_plural = "Weather Cache"
        ordering = ['-cached_at']


class EnergyLog(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='energy_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature_inside = models.FloatField()
    temperature_outside = models.FloatField()
    heating_power = models.FloatField(default=0)
    co2_saved = models.FloatField(default=0)

    class Meta:
        verbose_name = "Energy Log"
        verbose_name_plural = "Energy Logs"
        ordering = ['-timestamp']


class Recommendation(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='recommendations')
    message = models.TextField()
    recommended_action = models.CharField(max_length=200)
    estimated_savings = models.FloatField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.room.name}"

    class Meta:
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
        ordering = ['-priority', '-created_at']


class OccupancyPredictionModel(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100)
    accuracy = models.FloatField(default=0.0)
    trained_at = models.DateTimeField(auto_now=True)
    features_used = models.JSONField(default=list)  # ['day_of_week', 'time', 'weather', etc.]
    model_file = models.FileField(upload_to='ml_models/', null=True)

    def __str__(self):
        return f"{self.room.name} - {self.model_name} ({self.accuracy:.2%})"


class TrainingData(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    day_of_week = models.IntegerField()  # 0-6
    hour_of_day = models.IntegerField()  # 0-23
    temperature = models.FloatField()
    is_holiday = models.BooleanField()
    is_occupied = models.BooleanField()
    occupancy_duration = models.IntegerField()  # в минутах

    class Meta:
        indexes = [
            models.Index(fields=['room', 'timestamp']),
        ]


class EnergyChallenge(models.Model):
    """Энергетические челленджи для пользователей"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    target_savings = models.FloatField()  # kWh
    duration_days = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    reward_points = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Достижения пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(EnergyChallenge, on_delete=models.CASCADE, null=True)
    achievement_type = models.CharField(max_length=100, choices=[
        ('energy_saver', 'Energy Saver'),
        ('early_adopter', 'Early Adopter'),
        ('week_hero', 'Week Hero'),
        ('month_champion', 'Month Champion'),
    ])
    points_earned = models.IntegerField()
    earned_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)  # Дополнительные данные

    class Meta:
        unique_together = ['user', 'achievement_type', 'challenge']


class Leaderboard(models.Model):
    """Таблица лидеров"""
    period = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time')
    ])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField()
    energy_saved = models.FloatField()  # kWh
    co2_reduced = models.FloatField()  # kg
    rank = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['period', 'user']
        