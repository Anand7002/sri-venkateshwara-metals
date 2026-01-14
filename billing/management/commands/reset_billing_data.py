from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from billing.models import Invoice, InvoiceItem
from inventory.models import StockTransaction


class Command(BaseCommand):
    help = (
        'Permanently delete all invoice records, invoice line items, and any stock '
        'transactions created for invoices. Useful when you want to start fresh.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Confirm you really want to wipe all billing data.',
        )

    def handle(self, *args, **options):
        if not options['force']:
            raise CommandError(
                'This command will permanently delete all invoices, invoice items, and '
                'related stock transactions. Re-run with --force if you are sure.'
            )

        invoices = Invoice.objects.count()
        invoice_items = InvoiceItem.objects.count()
        invoice_txns = StockTransaction.objects.filter(note__startswith='Invoice ').count()

        with transaction.atomic():
            # Delete stock transactions first—signals will update item stock levels.
            StockTransaction.objects.filter(note__startswith='Invoice ').delete()
            InvoiceItem.objects.all().delete()
            Invoice.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Removed {invoices} invoices, {invoice_items} invoice items, '
                f'and {invoice_txns} invoice stock transactions.'
            )
        )

