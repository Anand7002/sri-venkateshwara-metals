from datetime import datetime
from decimal import Decimal

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_user.permissions import IsAdminRole

from billing.models import Invoice, InvoiceItem
from billing.serializers import InvoiceSerializer
from customers.models import Customer
from items.models import Item


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(value)
    except Exception:  # pragma: no cover - defensive
        return Decimal('0')


class DailySalesReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        start = _parse_date(request.query_params.get('start'))
        end = _parse_date(request.query_params.get('end'))

        invoices = Invoice.objects.all()
        if start:
            invoices = invoices.filter(date__date__gte=start)
        if end:
            invoices = invoices.filter(date__date__lte=end)

        payable_expr = F('total_amount') + F('gst_amount') - F('discount')
        aggregates = (
            invoices.annotate(day=TruncDate('date'))
            .values('day')
            .annotate(
                invoice_count=Count('id'),
                subtotal=Sum('total_amount'),
                gst_total=Sum('gst_amount'),
                discount_total=Sum('discount'),
                payable_total=Sum(
                    payable_expr,
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                ),
            )
            .order_by('-day')
        )

        results = [
            {
                'day': row['day'].isoformat(),
                'invoice_count': row['invoice_count'],
                'subtotal': float(row['subtotal'] or 0),
                'gst_total': float(row['gst_total'] or 0),
                'discount_total': float(row['discount_total'] or 0),
                'payable_total': float(row['payable_total'] or 0),
            }
            for row in aggregates
        ]

        summary = invoices.aggregate(
            invoice_count=Count('id'),
            subtotal=Sum('total_amount'),
            gst_total=Sum('gst_amount'),
            discount_total=Sum('discount'),
            payable_total=Sum(
                payable_expr,
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )

        payload = {
            'filters': {
                'start': start.isoformat() if start else None,
                'end': end.isoformat() if end else None,
            },
            'summary': {
                'invoice_count': summary['invoice_count'] or 0,
                'subtotal': float(summary['subtotal'] or 0),
                'gst_total': float(summary['gst_total'] or 0),
                'discount_total': float(summary['discount_total'] or 0),
                'payable_total': float(summary['payable_total'] or 0),
            },
            'results': results,
        }
        return Response(payload)


class StockReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        threshold = request.query_params.get('threshold')
        try:
            threshold = Decimal(str(threshold)) if threshold is not None else Decimal('5')
        except Exception:
            threshold = Decimal('5')
        search = request.query_params.get('search')

        items_qs = Item.objects.all().order_by('name')
        if search:
            items_qs = items_qs.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        report = []
        for item in items_qs:
            report.append(
                {
                    'item_id': item.id,
                    'name': item.name,
                    'sku': item.sku,
                    'unit': item.unit,
                    'total_in': float(item.total_in_stock or 0),
                    'total_out': float(item.total_out_stock or 0),
                    'current_stock': float(item.current_stock or 0),
                    'is_low_stock': (item.current_stock or Decimal('0')) <= threshold,
                }
            )

        return Response(
            {
                'threshold': float(threshold),
                'count': len(report),
                'results': report,
            }
        )


class CustomerSalesHistoryView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        invoices = Invoice.objects.filter(customer=customer).order_by('-date')

        payable_expr = F('total_amount') + F('gst_amount') - F('discount')
        summary = invoices.aggregate(
            invoice_count=Count('id'),
            subtotal=Sum('total_amount'),
            gst_total=Sum('gst_amount'),
            discount_total=Sum('discount'),
            payable_total=Sum(
                payable_expr,
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )

        serializer = InvoiceSerializer(invoices, many=True)
        return Response(
            {
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                    'email': customer.email,
                },
                'summary': {
                    'invoice_count': summary['invoice_count'] or 0,
                    'subtotal': float(summary['subtotal'] or 0),
                    'gst_total': float(summary['gst_total'] or 0),
                    'discount_total': float(summary['discount_total'] or 0),
                    'payable_total': float(summary['payable_total'] or 0),
                },
                'invoices': serializer.data,
            }
        )


class ItemSalesReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        start = _parse_date(request.query_params.get('start'))
        end = _parse_date(request.query_params.get('end'))
        search = request.query_params.get('search')

        invoice_items = InvoiceItem.objects.select_related('item', 'invoice')
        if start:
            invoice_items = invoice_items.filter(invoice__date__date__gte=start)
        if end:
            invoice_items = invoice_items.filter(invoice__date__date__lte=end)
        if search:
            invoice_items = invoice_items.filter(
                Q(item__name__icontains=search) | Q(item__sku__icontains=search)
            )

        line_total = ExpressionWrapper(
            F('price') * F('quantity'),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        gst_value = ExpressionWrapper(
            F('price') * F('quantity') * F('gst_percent') / 100,
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )

        aggregates = (
            invoice_items.values('item_id', 'item__name', 'item__sku', 'item__unit')
            .annotate(
                total_quantity=Sum('quantity'),
                subtotal=Sum(line_total),
                gst_total=Sum(gst_value),
                invoice_count=Count('invoice', distinct=True),
            )
            .order_by('-subtotal')
        )

        results = []
        total_quantity = Decimal('0')
        subtotal_sum = Decimal('0')
        gst_sum = Decimal('0')

        for row in aggregates:
            qty = _decimal(row['total_quantity'])
            subtotal = _decimal(row['subtotal'])
            gst_total = _decimal(row['gst_total'])
            total_quantity += qty
            subtotal_sum += subtotal
            gst_sum += gst_total

            results.append(
                {
                    'item_id': row['item_id'],
                    'name': row['item__name'],
                    'sku': row['item__sku'],
                    'unit': row['item__unit'],
                    'total_quantity': float(qty),
                    'subtotal': float(subtotal),
                    'gst_total': float(gst_total),
                    'invoice_count': row['invoice_count'],
                }
            )

        return Response(
            {
                'filters': {
                    'start': start.isoformat() if start else None,
                    'end': end.isoformat() if end else None,
                    'search': search or '',
                },
                'summary': {
                    'items': len(results),
                    'total_quantity': float(total_quantity),
                    'subtotal': float(subtotal_sum),
                    'gst_total': float(gst_sum),
                    'payable_total': float(subtotal_sum + gst_sum),
                },
                'results': results,
            }
        )

