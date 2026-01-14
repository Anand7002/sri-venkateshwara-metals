from django.db import models, transaction

from customers.models import Customer
from items.models import Item


class Invoice(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        PARTIAL = 'partial', 'Partial'

    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True
    )
    invoice_no = models.CharField(max_length=50, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.invoice_no


class InvoiceNumberSequence(models.Model):
    current = models.PositiveIntegerField(default=0)
    max_number = models.PositiveIntegerField(default=10000)

    class Meta:
        verbose_name = 'Invoice Number Tracker'
        verbose_name_plural = 'Invoice Number Tracker'

    def __str__(self):
        remaining = self.max_number - self.current
        return f'Current: {self.current} (Remaining: {remaining})'

    @classmethod
    def next_number(cls):
        """
        Return the next sequential invoice number.
        Starts at 1 and caps at max_number (default 10,000).
        """
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(pk=1, defaults={'current': 0})
            if seq.current >= seq.max_number:
                raise ValueError('Maximum invoice number reached. Please reset the tracker.')
            seq.current += 1
            seq.save(update_fields=['current'])
            return seq.current

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    def line_total(self):
        return (self.price * self.quantity)
