from decimal import Decimal

from django.conf import settings
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from items.models import Item
from notifications.services import notify_low_stock_alert

from .models import StockTransaction


def _threshold() -> Decimal:
    value = settings.NOTIFICATIONS.get('LOW_STOCK_THRESHOLD', Decimal('5'))
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:  # pragma: no cover - defensive
        return Decimal('5')


def _sync_current_stock(item_id):
    """
    Recalculate current_stock = total_in_stock - total_out_stock
    This ensures current_stock is always accurate after any stock transaction.
    """
    Item.objects.filter(pk=item_id).update(
        current_stock=F('total_in_stock') - F('total_out_stock')
    )


def _adjust_item_stock(item_id, txn_type, quantity):
    """
    Adjust stock totals based on transaction type.
    - IN: Increase total_in_stock
    - OUT: Increase total_out_stock (when customer purchases)
    Then recalculate current_stock = total_in_stock - total_out_stock
    """
    qty = Decimal(quantity)
    if qty == 0:
        return
    if txn_type == 'IN':
        Item.objects.filter(pk=item_id).update(total_in_stock=F('total_in_stock') + qty)
    else:
        # OUT transaction: customer purchase - increase total_out_stock
        Item.objects.filter(pk=item_id).update(total_out_stock=F('total_out_stock') + qty)
    # Recalculate current_stock after adjusting totals
    _sync_current_stock(item_id)


def _update_low_stock_status(item: Item):
    current_qty = Decimal(item.current_stock or 0)
    threshold = _threshold()
    if current_qty <= threshold and not item.low_stock_notified:
        notify_low_stock_alert(item, current_qty, threshold)
        Item.objects.filter(pk=item.pk).update(low_stock_notified=True)
    elif current_qty > threshold and item.low_stock_notified:
        Item.objects.filter(pk=item.pk).update(low_stock_notified=False)


@receiver(post_save, sender=StockTransaction)
def handle_stock_txn_created(sender, instance: StockTransaction, created, **kwargs):
    if created:
        _adjust_item_stock(instance.item_id, instance.txn_type, instance.quantity)
    instance.item.refresh_from_db(fields=['current_stock', 'low_stock_notified'])
    _update_low_stock_status(instance.item)


@receiver(post_delete, sender=StockTransaction)
def handle_stock_txn_deleted(sender, instance: StockTransaction, **kwargs):
    _adjust_item_stock(instance.item_id, instance.txn_type, -instance.quantity)
    instance.item.refresh_from_db(fields=['current_stock', 'low_stock_notified'])
    _update_low_stock_status(instance.item)
