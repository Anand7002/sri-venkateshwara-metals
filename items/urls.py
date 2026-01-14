from django.urls import path
from . import views
urlpatterns = [
    path('', views.ItemListCreate.as_view(), name='item-list-create'),
    path('<int:pk>/', views.ItemRetrieveUpdateDestroy.as_view(), name='item-rud'),
]
