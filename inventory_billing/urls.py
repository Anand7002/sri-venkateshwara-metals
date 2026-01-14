from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/items/', include('items.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/auth/', include('auth_user.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
]
