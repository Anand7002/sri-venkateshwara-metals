from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import StockTransaction, current_stock_for_item
from items.models import Item


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'item_link', 'txn_type_badge', 'quantity', 'note', 'created_at']
    list_filter = ['txn_type', 'created_at', 'item']
    search_fields = ['item__name', 'item__sku', 'note']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('item', 'txn_type', 'quantity', 'note')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def item_link(self, obj):
        """Link to the item with stock info"""
        url = reverse('admin:items_item_change', args=[obj.item.pk])
        current_stock = current_stock_for_item(obj.item)
        return format_html(
            '<a href="{}">{} ({})</a><br><small>Stock: {}</small>',
            url,
            obj.item.name,
            obj.item.sku,
            current_stock
        )
    item_link.short_description = 'Item'
    item_link.admin_order_field = 'item__name'
    
    def txn_type_badge(self, obj):
        """Display transaction type with color coding"""
        colors = {
            'IN': '#28a745',  # Green for IN
            'OUT': '#dc3545',  # Red for OUT
        }
        color = colors.get(obj.txn_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_txn_type_display()
        )
    txn_type_badge.short_description = 'Type'
    txn_type_badge.admin_order_field = 'txn_type'
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('item')
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure stock is recalculated"""
        super().save_model(request, obj, form, change)
        # Stock will be recalculated via signals, but we can also force it
        current_stock_for_item(obj.item)


# Note: Item admin is registered in items/admin.py

