INVOICE_TEMPLATE = {
    'subject': 'Invoice {invoice_no} - ₹{payable_amount:.2f}',
    'email': (
        'Dear {customer_name},\n\n'
        'Thank you for your purchase!\n\n'
        'Invoice Number: {invoice_no}\n'
        'Amount: ₹{payable_amount:.2f}\n'
        'Date: {date}\n\n'
        'Please find your invoice PDF attached for your records.\n\n'
        'If you have any questions, please contact us.\n\n'
        'Best regards,\n{sender}'
    ),
    'sms': (
        'Amount of invoice ₹{payable_amount:.2f}. Thank you.'
    ),
    'whatsapp': (
        '📄 *Invoice {invoice_no}*\n\n'
        'Amount: ₹{payable_amount:.2f}\n'
        'Date: {date}\n\n'
        'Download your invoice:\n{pdf_url}\n\n'
        'Thank you for your business!'
    ),
}

PAYMENT_TEMPLATE = {
    'subject': 'Payment Confirmation - Invoice {invoice_no}',
    'email': (
        'Dear {customer_name},\n\n'
        'We have received your payment!\n\n'
        'Invoice Number: {invoice_no}\n'
        'Amount Paid: ₹{amount:.2f}\n'
        'Payment Method: {method}\n'
        'Reference: {reference}\n'
        'Date: {date}\n'
        'Payment Status: {payment_status}\n\n'
        'Thank you for your payment.\n\n'
        'Best regards,\n{sender}'
    ),
    'sms': (
        'Payment confirmed: ₹{amount:.2f} via {method} for invoice {invoice_no}. '
        'Ref: {reference}. Status: {payment_status}'
    ),
    'whatsapp': (
        '✅ *Payment Confirmed*\n\n'
        'Invoice: {invoice_no}\n'
        'Amount: ₹{amount:.2f}\n'
        'Method: {method}\n'
        'Reference: {reference}\n'
        'Status: {payment_status}\n\n'
        'Thank you for your payment!'
    ),
}

LOW_STOCK_TEMPLATE = {
    'subject': '⚠️ Low Stock Alert: {item_name}',
    'email': (
        'Low Stock Alert\n\n'
        'Item: {item_name}\n'
        'SKU: {sku}\n'
        'Current Stock: {current_qty} {unit}\n'
        'Threshold: {threshold} {unit}\n\n'
        '⚠️ Stock is below the threshold. Please consider replenishing soon.\n\n'
        '— {sender}'
    ),
    'sms': (
        '⚠️ Low stock alert: {item_name} ({sku}) - {current_qty} {unit} remaining '
        '(threshold: {threshold} {unit}). Please restock soon.'
    ),
    'whatsapp': (
        '⚠️ *Low Stock Alert*\n\n'
        'Item: {item_name}\n'
        'SKU: {sku}\n'
        'Current: {current_qty} {unit}\n'
        'Threshold: {threshold} {unit}\n\n'
        'Please restock soon!'
    ),
}

TEMPLATES = {
    'invoice_created': INVOICE_TEMPLATE,
    'payment_confirmed': PAYMENT_TEMPLATE,
    'low_stock': LOW_STOCK_TEMPLATE,
}

