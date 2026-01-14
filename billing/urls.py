from django.urls import path

from . import views

urlpatterns = [
    path('', views.InvoiceListCreate.as_view(), name='invoice-list-create'),
    path('<int:pk>/', views.InvoiceDetail.as_view(), name='invoice-detail'),
    path(
        '<int:pk>/confirm-payment/',
        views.InvoicePaymentConfirmationView.as_view(),
        name='invoice-payment-confirm',
    ),
    path('<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice-pdf'),
]
