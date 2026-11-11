from django.db import models, transaction
from django.utils import timezone
import qrcode
from io import BytesIO
import base64


class Company(models.Model):
    COMPANY_TYPES = [
        ('Client', 'Client / Buyer'),
        ('Supplier', 'Supplier / Vendor'),
        ('Both', 'Both'),
    ]
    name = models.CharField(max_length=255, unique=True, help_text="e.g., Chipiku Plus City Centre, SANA Mega Store")
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPES, default='Client')
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Vegetables, Produce")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'Pieces / Units'),
        ('BOX', 'Boxes / Cartons'),
        ('BAG', 'Bags'),
        ('KG', 'Kilograms'),
        ('LTR', 'Liters'),
        ('SET', 'Sets / Bundles'),
    ]

    name = models.CharField(max_length=150, unique=True, help_text="e.g., Irish Potatoes, Carrots, Garlic")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    standard_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Default unit price")
    unit_of_measure = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')

    def __str__(self):
        return f"{self.name} ({self.unit_of_measure}) - MK {self.standard_price}"


class CashFlow(models.Model):
    TRANSACTION_TYPES = [
        ('Capital Input', 'Capital Input'),
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
    ]

    date = models.DateField(default=timezone.now)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.transaction_type}: MK {self.amount}"


class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Purchase / Buy'),
        ('SELL', 'Supply / Sell'),
    ]

    date = models.DateField(default=timezone.now)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='trades', help_text="Associated Company / Vendor")
    
    invoice_ref = models.CharField(max_length=50, blank=True, null=True, help_text="LPO or Invoice Number")
    
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional incidental costs")
    
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        company_name = self.company.name if self.company else "Cash/General"
        return f"{self.get_trade_type_display()} - {company_name} [{self.date}]"

    @property
    def items_subtotal(self):
        """Sum of all items attached to this trade."""
        return sum(item.total_price for item in self.trade_items.all())

    @property
    def grand_total(self):
        """Total cost/revenue including shared expenses."""
        if self.trade_type == 'BUY':
            return self.items_subtotal + self.transport_cost + self.labor_cost + self.other_expenses
        return self.items_subtotal


class TradeItem(models.Model):
    """Child model allowing multiple items per Trade transaction."""
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name='trade_items')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, help_text="Selected Inventory Item")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual buying or selling price per unit")

    def __str__(self):
        item_name = self.item.name if self.item else "Custom Item"
        return f"{item_name} ({self.quantity} @ {self.unit_price})"

    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Partial', 'Partial Payment'),
        ('Paid', 'Full Payment'),
        ('Overdue', 'Overdue'),
    ]

    trade = models.OneToOneField(Trade, on_delete=models.CASCADE, related_name='invoice', help_text="Associated trade transaction")
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, help_text="Auto-generated by system")
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    notes = models.TextField(blank=True, null=True, help_text="Payment terms or notes")

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.now()
            year_month = today.strftime('%Y%m')
            
            with transaction.atomic():
                last_invoice = Invoice.objects.select_for_update().filter(
                    invoice_number__startswith=f"INV-{year_month}"
                ).order_by('-id').first()
                
                if last_invoice:
                    try:
                        last_seq = int(last_invoice.invoice_number.split('-')[-1])
                        new_seq = last_seq + 1
                    except ValueError:
                        new_seq = 1
                else:
                    new_seq = 1
                self.invoice_number = f"INV-{year_month}-{new_seq:04d}"
                
        super().save(*args, **kwargs)

    def get_qr_code(self):
        """Generates a base64 encoded QR code containing transaction info."""
        client_name = self.trade.company.name if self.trade.company else "Cash Client"
        
        qr_data = (
            f"PISCES CO. INVOICE\n"
            f"Inv#: {self.invoice_number}\n"
            f"Client: {client_name}\n"
            f"Date: {self.issue_date}\n"
            f"Total: MWK {self.trade.grand_total:,.2f}"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def __str__(self):
        party = self.trade.company.name if self.trade.company else 'General'
        return f"Invoice {self.invoice_number} - {party}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
        ('Cheque', 'Cheque'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', blank=True, null=True)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, help_text="Auto-generated by system")
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Cash')
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction ID / Receipt Ref")
    notes = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            today = timezone.now()
            year_month = today.strftime('%Y%m')
            
            # Use atomic transaction to lock rows and prevent duplicate race conditions
            with transaction.atomic():
                last_payment = Payment.objects.select_for_update().filter(
                    receipt_number__startswith=f"REC-{year_month}"
                ).order_by('-id').first()
                
                if last_payment:
                    try:
                        last_seq = int(last_payment.receipt_number.split('-')[-1])
                        new_seq = last_seq + 1
                    except ValueError:
                        new_seq = 1
                else:
                    new_seq = 1
                
                self.receipt_number = f"REC-{year_month}-{new_seq:04d}"
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_number} - MK {self.amount} ({self.payment_method})"