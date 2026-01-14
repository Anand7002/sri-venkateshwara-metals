from django.db import models


class Item(models.Model):
    UNIT_CHOICES = [('pcs', 'pcs'), ('kg', 'kg'), ('meter', 'meter')]
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pcs')
    brand = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_in_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    total_out_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    current_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    low_stock_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"
