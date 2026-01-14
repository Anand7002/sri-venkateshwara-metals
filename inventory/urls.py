from django.urls import path

from . import views

urlpatterns = [
    path('txns/', views.StockTxnListCreate.as_view(), name='stock-txns'),
    path('current/', views.CurrentStockView.as_view(), name='current-stock'),
    path('report/', views.StockReportView.as_view(), name='stock-report'),
    path('low-stock/', views.LowStockAlertView.as_view(), name='low-stock'),
]
