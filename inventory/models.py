from decimal import Decimal

from django.db import models
from django.db.models import Q, Sum

from items.models import Item


class StockTransaction(models.Model):
    TXN_TYPES = (
        ('IN', 'Stock IN'),
        ('OUT', 'Stock OUT'),
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='txns')
    txn_type = models.CharField(max_length=3, choices=TXN_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.sku} {self.txn_type} {self.quantity}"

def _aggregate_stock(item_id: int) -> tuple[Decimal, Decimal]:
    """
    Aggregate total IN and OUT quantities directly from the stock transaction ledger.
    This acts as a single source of truth even if cached totals on Item get out-of-sync.
    """
    # Ensure item_id is an integer
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return Decimal('0'), Decimal('0')
    
    # Use separate queries to ensure correct aggregation
    # Using distinct() to avoid any potential duplicates
    total_in_result = StockTransaction.objects.filter(
        item_id=item_id, 
        txn_type='IN'
    ).aggregate(total=Sum('quantity'))
    
    total_out_result = StockTransaction.objects.filter(
        item_id=item_id, 
        txn_type='OUT'
    ).aggregate(total=Sum('quantity'))
    
    # Convert None to Decimal('0') and ensure Decimal type
    # Handle both None and Decimal types properly
    total_in_value = total_in_result.get('total')
    total_out_value = total_out_result.get('total')
    
    if total_in_value is None:
        total_in = Decimal('0')
    else:
        total_in = Decimal(str(total_in_value))
    
    if total_out_value is None:
        total_out = Decimal('0')
    else:
        total_out = Decimal(str(total_out_value))
    
    return total_in, total_out


def current_stock_for_item(item):
    """
    Returns current stock for an item by aggregating from the transaction ledger.
    This ensures we always get the most accurate stock count, even if cached fields
    are temporarily out of sync. The ledger is the single source of truth.
    
    Accepts either an Item instance or an item ID (int).
    """
    # Handle both Item instance and item ID
    if hasattr(item, 'pk'):
        item_id = item.pk
    elif hasattr(item, 'id'):
        item_id = item.id
    else:
        try:
            item_id = int(item)
        except (ValueError, TypeError):
            return Decimal('0')
    
    if not item_id:
        return Decimal('0')

    # Always aggregate from the ledger to ensure accuracy
    total_in, total_out = _aggregate_stock(item_id)
    current = total_in - total_out
    
    # Sync cached fields so subsequent reads are fast and consistent
    # Only update if the item exists
    try:
        Item.objects.filter(pk=item_id).update(
            total_in_stock=total_in,
            total_out_stock=total_out,
            current_stock=current,
        )
    except Exception:
        # If update fails, still return the calculated value
        pass
    
    return current
