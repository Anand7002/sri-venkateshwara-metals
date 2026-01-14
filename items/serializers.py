from rest_framework import serializers
from .models import Item
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = [
            'low_stock_notified',
            'total_in_stock',
            'total_out_stock',
            'current_stock',
        ]
