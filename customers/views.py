from rest_framework import generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from billing.models import Invoice
from billing.serializers import InvoiceSerializer

from auth_user.permissions import IsAdminOrCashier

from .models import Customer
from .serializers import CustomerSerializer


class CustomerListCreate(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by('-id')
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone']
    permission_classes = [IsAdminOrCashier]


class CustomerRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrCashier]


@api_view(['GET'])
@permission_classes([IsAdminOrCashier])
def customer_history(request, pk):
    invoices = Invoice.objects.filter(customer_id=pk).order_by('-date')
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)
