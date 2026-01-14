from django.contrib import admin

from .models import InvoiceNumberSequence


@admin.register(InvoiceNumberSequence)
class InvoiceNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ('current', 'max_number', 'remaining')
    readonly_fields = ('current', 'max_number', 'remaining')

    def remaining(self, obj):
        return max(obj.max_number - obj.current, 0)

    remaining.short_description = 'Remaining numbers'

    def has_add_permission(self, request):
        # Allow only one tracker entry
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

