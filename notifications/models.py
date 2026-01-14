from django.db import models


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    class Event(models.TextChoices):
        INVOICE_CREATED = 'invoice_created', 'Invoice Created'
        PAYMENT_CONFIRMED = 'payment_confirmed', 'Payment Confirmed'
        LOW_STOCK = 'low_stock', 'Low Stock Alert'

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    event = models.CharField(max_length=50, choices=Event.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} → {self.recipient} ({self.channel})"

