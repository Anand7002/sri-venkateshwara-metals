import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List

from django.conf import settings
from django.utils import timezone

from billing.models import Invoice
from items.models import Item

from .models import NotificationLog
from .providers import (
    ConsoleProvider,
    EmailProvider,
    NotificationSendError,
    TwilioProvider,
)
from .templates import TEMPLATES

logger = logging.getLogger(__name__)


@dataclass
class Recipient:
    channel: str
    address: str


def _get_sender():
    return settings.NOTIFICATIONS.get('SENDER_NAME', 'Inventory & Billing System')


def _get_base_url():
    """Get the base URL for generating absolute links in notifications."""
    base_url = settings.NOTIFICATIONS.get('BASE_URL', 'http://localhost:8000')
    return base_url.rstrip('/')


def _render(event_key: str, channel: str, context: dict):
    template = TEMPLATES[event_key]
    subject = template.get('subject', '').format(**context)
    body_template = template.get(channel) or template.get('email') or template.get('sms')
    message = body_template.format(**context)
    return subject, message


def _log_delivery(
    event_key: str,
    recipient: Recipient,
    subject: str,
    message: str,
    status: str,
    error: str = '',
    metadata=None,
):
    NotificationLog.objects.create(
        event=event_key,
        channel=recipient.channel,
        recipient=recipient.address,
        subject=subject,
        message=message,
        status=status,
        error=error,
        metadata=metadata or {},
    )


def _provider_for(channel: str):
    config = settings.NOTIFICATIONS.get('CHANNELS', {}).get(channel, {})
    if channel == NotificationLog.Channel.EMAIL:
        return EmailProvider(channel, config)
    provider_name = config.get('provider')
    if provider_name == 'twilio':
        return TwilioProvider(channel, config)
    return ConsoleProvider(channel, config)


def _dispatch(
    event_key: str,
    recipients: Iterable[Recipient],
    context: dict,
    metadata=None,
    attachments=None,
):
    """Dispatch notifications to all recipients, logging each attempt."""
    if not recipients:
        logger.warning(f"No recipients found for event: {event_key}")
        return
    
    for recipient in recipients:
        try:
            subject, message = _render(event_key, recipient.channel, context)
        except KeyError as e:
            logger.error(f"Template missing key for {event_key}: {e}")
            error = f"Template error: {str(e)}"
            _log_delivery(
                event_key,
                recipient,
                '',
                '',
                NotificationLog.Status.FAILED,
                error,
                metadata=metadata,
            )
            continue
        except Exception as e:
            logger.error(f"Error rendering template for {event_key}: {e}")
            error = f"Template rendering error: {str(e)}"
            _log_delivery(
                event_key,
                recipient,
                '',
                '',
                NotificationLog.Status.FAILED,
                error,
                metadata=metadata,
            )
            continue
        
        provider = _provider_for(recipient.channel)
        channel_attachments = None
        if attachments:
            channel_attachments = attachments.get(recipient.channel) or attachments.get('default')
        status = NotificationLog.Status.SENT
        error = ''
        try:
            provider.send(recipient.address, subject, message, attachments=channel_attachments)
            logger.info(f"Notification sent: {event_key} → {recipient.channel}:{recipient.address}")
        except NotificationSendError as exc:
            status = NotificationLog.Status.FAILED
            error = str(exc)
            logger.error(f"Notification failed: {event_key} → {recipient.channel}:{recipient.address} - {error}")
        except Exception as exc:
            status = NotificationLog.Status.FAILED
            error = f"Unexpected error: {str(exc)}"
            logger.exception(f"Unexpected error sending notification: {event_key} → {recipient.channel}:{recipient.address}")
        
        _log_delivery(
            event_key,
            recipient,
            subject,
            message,
            status,
            error,
            metadata=metadata,
        )


def _customer_recipients(customer) -> List[Recipient]:
    if not customer:
        return []
    recipients = []
    if customer.email:
        recipients.append(Recipient('email', customer.email))
    return recipients


def _admin_recipients():
    config = settings.NOTIFICATIONS.get('ADMIN_CONTACTS', {})
    recipients = []
    for address in config.get('email', []):
        address = (address or '').strip()
        if address:
            recipients.append(Recipient('email', address))
    return recipients


def notify_invoice_created(invoice: Invoice):
    """Send notification when a new invoice is created."""
    event = NotificationLog.Event.INVOICE_CREATED
    base_url = _get_base_url()
    pdf_url = f"{base_url}/api/billing/{invoice.id}/pdf/"
    
    context = {
        'invoice_no': invoice.invoice_no,
        'customer_name': invoice.customer.name if invoice.customer else 'Customer',
        'payable_amount': float(invoice.total_amount + invoice.gst_amount - invoice.discount),
        'date': invoice.date.strftime('%d-%b-%Y %H:%M'),
        'pdf_url': pdf_url,
        'sender': _get_sender(),
    }
    recipients = _customer_recipients(invoice.customer)
    if not recipients:
        recipients = _admin_recipients()
    attachments = {}
    try:
        from billing.invoice_generator import generate_invoice_pdf

        pdf_buffer = generate_invoice_pdf(invoice)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        attachments['email'] = [
            {
                'filename': f'{invoice.invoice_no}.pdf',
                'content': pdf_bytes,
                'mimetype': 'application/pdf',
            }
        ]
    except Exception as exc:
        logger.error('Failed to generate invoice PDF attachment: %s', exc)
    if recipients:
        _dispatch(
            event,
            recipients,
            context,
            metadata={'invoice_id': invoice.id},
            attachments=attachments or None,
        )
    else:
        logger.warning(f"No recipients found for invoice {invoice.invoice_no}")


def notify_payment_confirmation(invoice: Invoice, payment_data: dict):
    """Send notification when a payment is confirmed."""
    event = NotificationLog.Event.PAYMENT_CONFIRMED
    context = {
        'invoice_no': invoice.invoice_no,
        'customer_name': invoice.customer.name if invoice.customer else 'Customer',
        'amount': float(payment_data['amount']),
        'method': payment_data['method'],
        'reference': payment_data.get('reference', '') or 'N/A',
        'date': timezone.now().strftime('%d-%b-%Y %H:%M'),
        'payment_status': invoice.get_payment_status_display(),
        'sender': _get_sender(),
    }
    recipients = _customer_recipients(invoice.customer) or _admin_recipients()
    if recipients:
        _dispatch(event, recipients, context, metadata={'invoice_id': invoice.id})
    else:
        logger.warning(f"No recipients found for payment confirmation on invoice {invoice.invoice_no}")


def notify_low_stock_alert(item: Item, current_qty: Decimal, threshold: Decimal):
    """Send notification when an item's stock falls below threshold."""
    event = NotificationLog.Event.LOW_STOCK
    context = {
        'item_name': item.name,
        'sku': item.sku,
        'unit': item.unit,
        'current_qty': float(current_qty),
        'threshold': float(threshold),
        'sender': _get_sender(),
    }
    recipients = _admin_recipients()
    if recipients:
        _dispatch(event, recipients, context, metadata={'item_id': item.id})
    else:
        logger.warning(f"No admin recipients configured for low stock alert on item {item.sku}")

