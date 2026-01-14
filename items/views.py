from rest_framework import generics, filters

from auth_user.permissions import IsAdminOrReadOnly

from .models import Item
from .serializers import ItemSerializer


class ItemListCreate(generics.ListCreateAPIView):
    queryset = Item.objects.all().order_by('-id')
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'sku']
    permission_classes = [IsAdminOrReadOnly]


class ItemRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAdminOrReadOnly]
