from django.contrib import admin
from .models import Building, Room, OccupancyLog, WeatherCache, EnergyLog, Recommendation


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'total_area')
    search_fields = ('name', 'address')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'area', 'wall_material', 'heating_status', 'get_heat_loss_factor')
    list_filter = ('building', 'wall_material', 'heating_status')
    search_fields = ('name', 'building__name')
    list_editable = ('heating_status',)

    def get_heat_loss_factor(self, obj):
        return f"{obj.get_heat_loss_factor():.2f}"

    get_heat_loss_factor.short_description = 'Heat Loss Factor'


@admin.register(OccupancyLog)
class OccupancyLogAdmin(admin.ModelAdmin):
    list_display = ('room', 'start_time', 'end_time', 'is_active', 'duration_minutes', 'is_currently_occupied')
    list_filter = ('room', 'is_active')
    search_fields = ('room__name', 'purpose')
    date_hierarchy = 'start_time'


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ('temperature', 'humidity', 'description', 'cached_at', 'is_expired')
    readonly_fields = ('cached_at',)

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = 'Expired?'


@admin.register(EnergyLog)
class EnergyLogAdmin(admin.ModelAdmin):
    list_display = ('room', 'timestamp', 'temperature_inside', 'temperature_outside', 'heating_power', 'co2_saved')
    list_filter = ('room', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('room', 'message', 'priority', 'is_applied', 'created_at')
    list_filter = ('priority', 'is_applied', 'room')
    list_editable = ('is_applied',)
    actions = ['mark_as_applied']

    def mark_as_applied(self, request, queryset):
        updated = queryset.update(is_applied=True, applied_at=timezone.now())
        self.message_user(request, f"{updated} recommendations marked as applied.")

    mark_as_applied.short_description = "Mark selected recommendations as applied"