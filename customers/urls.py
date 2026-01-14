from django.urls import path

from . import views

urlpatterns = [
    path('', views.CustomerListCreate.as_view(), name='customer-list-create'),
    path('<int:pk>/', views.CustomerRetrieveUpdateDestroy.as_view(), name='customer-rud'),
    path('<int:pk>/history/', views.customer_history, name='customer-history'),
]
