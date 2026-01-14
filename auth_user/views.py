from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminRole
from .serializers import ProfileSerializer, UserManagementSerializer

User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('username').select_related('userrole')
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminRole]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all().select_related('userrole')
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminRole]

