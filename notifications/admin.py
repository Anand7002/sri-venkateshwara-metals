from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'event',
        'channel',
        'recipient',
        'status',
        'created_at',
    ]
    list_filter = ['event', 'channel', 'status', 'created_at']
    search_fields = ['recipient', 'subject', 'message', 'metadata']
    readonly_fields = [
        'event',
        'channel',
        'recipient',
        'subject',
        'message',
        'status',
        'error',
        'metadata',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def has_add_permission(self, request):
        """Notifications are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Notifications are read-only logs."""
        return False

