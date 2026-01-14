from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from auth_user.permissions import IsAdminOrCashier

from .models import Invoice
from .serializers import InvoiceSerializer, PaymentConfirmationSerializer
from .invoice_generator import generate_invoice_pdf


class InvoiceListCreate(generics.ListCreateAPIView):
    queryset = Invoice.objects.all().order_by('-date')
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrCashier]


class InvoiceDetail(generics.RetrieveAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrCashier]


class InvoicePaymentConfirmationView(APIView):
    permission_classes = [IsAdminOrCashier]

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        serializer = PaymentConfirmationSerializer(
            data=request.data, context={'invoice': invoice}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        refreshed = Invoice.objects.get(pk=invoice.pk)
        return Response(InvoiceSerializer(refreshed).data)


class InvoicePDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        invoice = get_object_or_404(
            Invoice.objects.select_related('customer').prefetch_related('items__item'),
            pk=pk,
        )
        buffer = generate_invoice_pdf(invoice)
        filename = f'{invoice.invoice_no}.pdf'
        return FileResponse(buffer, as_attachment=True, filename=filename)
