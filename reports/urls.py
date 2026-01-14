from django.urls import path

from . import views

urlpatterns = [
    path('sales/daily/', views.DailySalesReportView.as_view(), name='daily-sales-report'),
    path('stock/', views.StockReportView.as_view(), name='stock-report'),
    path(
        'sales/customers/<int:pk>/',
        views.CustomerSalesHistoryView.as_view(),
        name='customer-sales-history',
    ),
    path('sales/items/', views.ItemSalesReportView.as_view(), name='item-sales-report'),
]
