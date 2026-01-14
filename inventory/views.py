from decimal import Decimal

from django.db.models import Q, Sum, Case, When, DecimalField, F, BooleanField
from django.db.models.functions import Coalesce
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_user.permissions import IsAdminOrCashier, IsAdminOrReadOnly
from items.models import Item

from .models import StockTransaction, current_stock_for_item
from .serializers import StockTransactionSerializer


class StockTxnListCreate(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        """List stock transactions"""
        queryset = StockTransaction.objects.select_related('item').order_by('-created_at')
        item_id = request.query_params.get('item')
        txn_type = request.query_params.get('txn_type')
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if txn_type in ('IN', 'OUT'):
            queryset = queryset.filter(txn_type=txn_type)
        limit = request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                if limit > 0:
                    queryset = queryset[:limit]
            except (TypeError, ValueError):
                pass
        
        serializer = StockTransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        item_id = request.data.get('item')
        txn_type = request.data.get('txn_type')
        quantity = request.data.get('quantity')
        note = request.data.get('note', '')

        # Validate required fields
        if not item_id:
            return Response(
                {'detail': 'Item is required.'},
                status=400
            )
        if not txn_type:
            return Response(
                {'detail': 'Transaction type is required.'},
                status=400
            )
        if not quantity:
            return Response(
                {'detail': 'Quantity is required.'},
                status=400
            )

        # Convert item_id to int if it's a string
        try:
            item_id = int(item_id) if item_id else None
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Invalid item ID.'},
                status=400
            )

        try:
            qty = Decimal(quantity)
            if qty <= 0:
                return Response(
                    {'detail': 'Quantity must be greater than zero.'},
                    status=400
                )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Invalid quantity value.'},
                status=400
            )

        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response(
                {'detail': 'Item not found.'},
                status=404
            )

        # Check stock before OUT using the centralized function
        if txn_type == 'OUT':
            current_stock = current_stock_for_item(item)
            if qty > current_stock:
                return Response(
                    {'detail': f'Cannot OUT {qty}. Only {current_stock} in stock.'},
                    status=400
                )

        StockTransaction.objects.create(
            item=item,
            txn_type=txn_type,
            quantity=qty,
            note=note
        )

        return Response({'status': 'success'})


def _parse_threshold(value, default='5'):
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


class StockReportView(APIView):
    permission_classes = [IsAdminOrCashier]

    def get(self, request):
        threshold = _parse_threshold(request.GET.get('threshold', 5))
        search = request.GET.get('search')

        items = Item.objects.all()

        if search:
            items = items.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        report = items.annotate(
            total_in=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='IN', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
            total_out=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='OUT', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
        ).annotate(
            calculated_current_stock=F('total_in') - F('total_out'),
            is_low_stock=Case(
                When(calculated_current_stock__lte=threshold, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).values(
            'id', 'name', 'sku', 'unit',
            'total_in', 'total_out', 'calculated_current_stock', 'is_low_stock'
        ).order_by('name')

        # Convert to list and format for frontend (item_id instead of id)
        report_list = []
        for row in report:
            report_list.append({
                'item_id': row['id'],
                'name': row['name'],
                'sku': row['sku'],
                'unit': row['unit'],
                'total_in': float(row['total_in'] or 0),
                'total_out': float(row['total_out'] or 0),
                'current_stock': float(row['calculated_current_stock'] or 0),
                'is_low_stock': row['is_low_stock'],
            })

        return Response({
            'threshold': threshold,
            'count': len(report_list),
            'results': report_list
        })


class LowStockAlertView(APIView):
    permission_classes = [IsAdminOrCashier]

    def get(self, request):
        threshold = _parse_threshold(request.GET.get('threshold', 5))

        items = Item.objects.all()

        report = items.annotate(
            total_in=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='IN', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
            total_out=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='OUT', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
        ).annotate(
            calculated_current_stock=F('total_in') - F('total_out'),
            is_low_stock=Case(
                When(calculated_current_stock__lte=threshold, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).filter(is_low_stock=True).values(
            'id', 'name', 'sku', 'unit',
            'total_in', 'total_out', 'calculated_current_stock', 'is_low_stock'
        ).order_by('name')

        # Convert to list and format for frontend
        report_list = []
        for row in report:
            report_list.append({
                'item_id': row['id'],
                'name': row['name'],
                'sku': row['sku'],
                'unit': row['unit'],
                'total_in': float(row['total_in'] or 0),
                'total_out': float(row['total_out'] or 0),
                'current_stock': float(row['calculated_current_stock'] or 0),
                'is_low_stock': row['is_low_stock'],
            })

        return Response({
            'threshold': threshold,
            'count': len(report_list),
            'results': report_list
        })


class CurrentStockView(APIView):
    permission_classes = [IsAdminOrCashier]

    def get(self, request):
        threshold = _parse_threshold(request.GET.get('threshold', 5))

        items = Item.objects.all()

        report = items.annotate(
            total_in=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='IN', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
            total_out=Coalesce(
                Sum(
                    Case(
                        When(txns__txn_type='OUT', then=F('txns__quantity')),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                0,
                output_field=DecimalField()
            ),
        ).annotate(
            calculated_current_stock=F('total_in') - F('total_out'),
            is_low_stock=Case(
                When(calculated_current_stock__lte=threshold, then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).values(
            'id', 'name', 'sku', 'unit',
            'total_in', 'total_out', 'calculated_current_stock', 'is_low_stock'
        ).order_by('name')

        # Convert to list and format for frontend
        report_list = []
        for row in report:
            report_list.append({
                'item_id': row['id'],
                'name': row['name'],
                'sku': row['sku'],
                'unit': row['unit'],
                'total_in': float(row['total_in'] or 0),
                'total_out': float(row['total_out'] or 0),
                'current_stock': float(row['calculated_current_stock'] or 0),
                'is_low_stock': row['is_low_stock'],
            })

        return Response(report_list)
