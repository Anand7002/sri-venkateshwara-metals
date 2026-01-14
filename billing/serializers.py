from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from inventory.models import StockTransaction, current_stock_for_item
from items.models import Item
from notifications.services import (
    notify_invoice_created,
    notify_payment_confirmation,
)

from .models import Invoice, InvoiceItem, InvoiceNumberSequence


class InvoiceItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ['id', 'item', 'item_name', 'item_sku', 'quantity', 'price', 'gst_percent']
        read_only_fields = ['id', 'item_name', 'item_sku']
        extra_kwargs = {
            'price': {'required': False},
            'gst_percent': {'required': False},
        }

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be positive.')
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    payable_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_no',
            'customer',
            'customer_name',
            'date',
            'total_amount',
            'gst_amount',
            'discount',
            'payment_status',
            'paid_amount',
            'payment_method',
            'payment_reference',
            'paid_at',
            'payable_amount',
            'items',
        ]
        read_only_fields = [
            'id',
            'invoice_no',
            'date',
            'total_amount',
            'gst_amount',
            'payable_amount',
            'payment_status',
            'paid_amount',
            'paid_at',
        ]

    def get_payable_amount(self, obj):
        return float(obj.total_amount + obj.gst_amount - obj.discount)

    def _generate_invoice_no(self):
        next_number = InvoiceNumberSequence.next_number()
        return f'{next_number}'

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not items_data:
            raise serializers.ValidationError({'items': 'At least one line item is required.'})

        discount = Decimal(validated_data.get('discount') or 0)
        if not validated_data.get('invoice_no'):
            validated_data['invoice_no'] = self._generate_invoice_no()

        invoice = Invoice.objects.create(**validated_data)
        subtotal = Decimal('0')
        gst_total = Decimal('0')

        for item_payload in items_data:
            item = item_payload['item']
            # Ensure item is a proper Item instance - DRF should resolve this, but be defensive
            if not isinstance(item, Item):
                # If it's an ID, fetch the item from database
                try:
                    item_id = int(item) if not hasattr(item, 'pk') else (item.pk or item.id if hasattr(item, 'id') else item)
                    item = Item.objects.select_for_update().get(pk=item_id)
                except (ValueError, TypeError, Item.DoesNotExist):
                    raise serializers.ValidationError(
                        {'items': f'Invalid item: {item}'}
                    )
            else:
                # Refresh from database to ensure we have latest data
                item.refresh_from_db()
            
            quantity = Decimal(item_payload['quantity'])
            price = Decimal(
                item_payload.get('price') if item_payload.get('price') is not None else item.price
            )
            gst_percent = Decimal(
                item_payload.get('gst_percent')
                if item_payload.get('gst_percent') is not None
                else item.gst_percent
            )

            # Calculate available stock - this queries the transaction ledger directly
            available = current_stock_for_item(item)
            if quantity > available:
                error_msg = f'Not enough stock for {item.name} ({item.sku}). Available: {available}'
                if available == 0:
                    error_msg += '. Please add Stock IN transactions first.'
                raise serializers.ValidationError({'items': error_msg})

            line_total = price * quantity
            gst_amount = (line_total * gst_percent) / Decimal('100')
            subtotal += line_total
            gst_total += gst_amount

            InvoiceItem.objects.create(
                invoice=invoice,
                item=item,
                quantity=quantity,
                price=price,
                gst_percent=gst_percent,
            )
            StockTransaction.objects.create(
                item=item,
                txn_type='OUT',
                quantity=quantity,
                note=f'Invoice {invoice.invoice_no}',
            )

        if discount < 0:
            raise serializers.ValidationError({'discount': 'Discount cannot be negative.'})
        if discount > (subtotal + gst_total):
            raise serializers.ValidationError({'discount': 'Discount exceeds invoice total.'})

        invoice.total_amount = subtotal
        invoice.gst_amount = gst_total
        invoice.save()

        notify_invoice_created(invoice)

        return invoice


class PaymentConfirmationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    method = serializers.CharField(max_length=50)
    reference = serializers.CharField(max_length=100, allow_blank=True, required=False)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def save(self, **kwargs):
        invoice: Invoice = self.context['invoice']
        amount = Decimal(self.validated_data['amount'])
        method = self.validated_data['method']
        reference = self.validated_data.get('reference', '')

        due = invoice.total_amount + invoice.gst_amount - invoice.discount
        if amount >= due:
            invoice.payment_status = Invoice.PaymentStatus.PAID
        else:
            invoice.payment_status = Invoice.PaymentStatus.PARTIAL

        invoice.paid_amount = amount
        invoice.payment_method = method
        invoice.payment_reference = reference
        invoice.paid_at = timezone.now()
        invoice.save(
            update_fields=[
                'payment_status',
                'paid_amount',
                'payment_method',
                'payment_reference',
                'paid_at',
            ]
        )

        notify_payment_confirmation(
            invoice,
            {
                'amount': amount,
                'method': method,
                'reference': reference,
            },
        )

        return invoice
