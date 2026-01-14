from django.contrib import admin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Sum
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'phone',
        'email',
        'invoice_count_display',
        'lifetime_value_display',
        'last_invoice_display',
        'created_at',
    )
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'last_invoice_summary', 'lifetime_value_display', 'invoice_count_display')
    ordering = ('name',)
    fieldsets = (
        ('Contact Information', {'fields': ('name', 'phone', 'email', 'address')}),
        ('Billing Snapshot', {'fields': ('invoice_count_display', 'lifetime_value_display', 'last_invoice_summary')}),
        ('Metadata', {'fields': ('created_at',)}),
    )
    actions = ['export_contacts']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        billed_amount = ExpressionWrapper(
            F('invoice__total_amount') + F('invoice__gst_amount') - F('invoice__discount'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        return queryset.annotate(
            invoice_count=Count('invoice', distinct=True),
            lifetime_value=Sum(billed_amount, distinct=False),
            last_invoice_date=Max('invoice__date'),
        )

    @admin.display(description='Invoices', ordering='invoice_count')
    def invoice_count_display(self, obj):
        return obj.invoice_count or 0

    @admin.display(description='Total Billed', ordering='lifetime_value')
    def lifetime_value_display(self, obj):
        amount = obj.lifetime_value or 0
        return f'₹{amount:,.2f}'

    @admin.display(description='Last Invoice', ordering='last_invoice_date')
    def last_invoice_display(self, obj):
        if not obj.last_invoice_date:
            return '—'
        return obj.last_invoice_date.strftime('%d %b %Y %I:%M %p')

    @admin.display(description='Last Invoice Snapshot')
    def last_invoice_summary(self, obj):
        if not obj.last_invoice_date:
            return 'No invoices yet.'
        return format_html(
            '<div style="background:#f8f9fa;border-radius:4px;padding:8px;">'
            '<strong>Date:</strong> {}<br>'
            '<strong>Total billed so far:</strong> {}<br>'
            '<strong>Invoices created:</strong> {}'
            '</div>',
            obj.last_invoice_date.strftime('%d %b %Y %I:%M %p'),
            self.lifetime_value_display(obj),
            self.invoice_count_display(obj),
        )

    @admin.action(description='Export selected contacts (CSV)')
    def export_contacts(self, request, queryset):
        headers = ('Name', 'Phone', 'Email', 'Address', 'Invoices', 'Total Billed')
        rows = [headers]
        for customer in queryset:
            rows.append(
                (
                    customer.name,
                    customer.phone,
                    customer.email or '',
                    customer.address or '',
                    customer.invoice_count or 0,
                    customer.lifetime_value or 0,
                )
            )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=customers.csv'
        response.write('\ufeff')  # UTF-8 BOM for Excel
        for row in rows:
            response.write(','.join(f'"{str(value).replace(chr(34), chr(34)*2)}"' for value in row))
            response.write('\n')
        return response


admin.site.register(Customer, CustomerAdmin)

