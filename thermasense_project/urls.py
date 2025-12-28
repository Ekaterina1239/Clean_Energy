from django.contrib import admin
from django.urls import path, include

from dashboard.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/login/', dashboard),

    path('', dashboard, name='dashboard'),
    path('dashboard/', include('dashboard.urls')),
    path('core/', include('core.urls')),
]