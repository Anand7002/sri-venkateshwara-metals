from django.urls import path
from rest_framework import generics

from auth_user.permissions import IsAdminRole

from .models import NotificationLog
from .serializers import NotificationLogSerializer


class NotificationLogList(generics.ListAPIView):
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAdminRole]


urlpatterns = [
    path('logs/', NotificationLogList.as_view(), name='notification-logs'),
]
