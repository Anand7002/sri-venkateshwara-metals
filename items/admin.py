from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Item
from inventory.models import StockTransaction, current_stock_for_item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sku', 'unit', 'price', 'stock_info', 'low_stock_indicator', 'created_at']
    list_filter = ['unit', 'low_stock_notified', 'created_at']
    search_fields = ['name', 'sku', 'brand']
    readonly_fields = ['created_at', 'updated_at', 'stock_summary']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'unit', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'gst_percent')
        }),
        ('Stock Information', {
            'fields': ('stock_summary', 'total_in_stock', 'total_out_stock', 'current_stock', 'low_stock_notified'),
            'description': 'Stock values are calculated from transactions. Use Stock Transactions to add stock.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_info(self, obj):
        """Display current stock with color coding"""
        current = current_stock_for_item(obj)
        if current <= 0:
            color = '#dc3545'  # Red
            text = f'{current}'
        elif current <= 5:
            color = '#ffc107'  # Yellow/Orange
            text = f'{current}'
        else:
            color = '#28a745'  # Green
            text = f'{current}'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    stock_info.short_description = 'Current Stock'
    stock_info.admin_order_field = 'current_stock'
    
    def low_stock_indicator(self, obj):
        """Show low stock warning"""
        current = current_stock_for_item(obj)
        if current <= 5:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 11px;">LOW</span>'
            )
        return format_html('<span style="color: #6c757d;">—</span>')
    low_stock_indicator.short_description = 'Status'
    
    def stock_summary(self, obj):
        """Show detailed stock summary"""
        current = current_stock_for_item(obj)
        total_in = obj.total_in_stock or 0
        total_out = obj.total_out_stock or 0
        
        # Count transactions
        in_count = StockTransaction.objects.filter(item=obj, txn_type='IN').count()
        out_count = StockTransaction.objects.filter(item=obj, txn_type='OUT').count()
        
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 4px;">'
            '<strong>Stock Summary:</strong><br>'
            'Current Stock: <strong>{}</strong><br>'
            'Total IN: {} ({} transactions)<br>'
            'Total OUT: {} ({} transactions)<br>'
            '<a href="/admin/inventory/stocktransaction/?item__id__exact={}" style="margin-top: 5px; display: inline-block;">View All Transactions →</a>'
            '</div>',
            current,
            total_in,
            in_count,
            total_out,
            out_count,
            obj.pk
        )
    stock_summary.short_description = 'Stock Details'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('txns')
    
    actions = ['sync_stock_values']
    
    def sync_stock_values(self, request, queryset):
        """Admin action to sync stock values from transactions"""
        count = 0
        for item in queryset:
            current_stock_for_item(item)
            count += 1
        self.message_user(request, f'Successfully synced stock for {count} item(s).')
    sync_stock_values.short_description = 'Sync stock values from transactions'
