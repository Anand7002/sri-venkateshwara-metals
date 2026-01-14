from rest_framework import serializers
from .models import StockTransaction, current_stock_for_item


class StockTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)

    class Meta:
        model = StockTransaction
        fields = [
            'id',
            'item',
            'item_name',
            'item_sku',
            'txn_type',
            'quantity',
            'note',
            'created_at',
        ]
        read_only_fields = ['id', 'item_name', 'item_sku', 'created_at']

    def validate(self, attrs):
        item = attrs.get('item') or getattr(self.instance, 'item', None)
        txn_type = attrs.get('txn_type') or getattr(self.instance, 'txn_type', None)
        quantity = attrs.get('quantity')
        if txn_type == 'OUT' and item and quantity:
            available = current_stock_for_item(item)
            if quantity > available:
                raise serializers.ValidationError(
                    {'quantity': f'Not enough stock. Available: {available}'}
                )
        return attrs
