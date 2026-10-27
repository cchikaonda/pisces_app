from django.db import models
from django.utils import timezone

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
        return f"{self.date} - {self.transaction_type}: ${self.amount}"


class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Purchase / Buy'),
        ('SELL', 'Supply / Sell'),
    ]

    UNIT_CHOICES = [
        ('PCS', 'Pieces / Units'),
        ('BOX', 'Boxes / Cartons'),
        ('BAG', 'Bags'),
        ('KG', 'Kilograms'),
        ('LTR', 'Liters'),
        ('SET', 'Sets / Bundles'),
    ]

    date = models.DateField(default=timezone.now)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    category = models.CharField(max_length=100, help_text="e.g., Office Stationery, Hardware, Electronics")
    item_name = models.CharField(max_length=150)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_of_measure = models.CharField(max_length=10, choices=UNIT_CHOICES, default='PCS')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Buying or Selling price per unit")
    
    party_name = models.CharField(max_length=150, blank=True, null=True, help_text="Supplier Name or Client/Organization Name")
    invoice_ref = models.CharField(max_length=50, blank=True, null=True, help_text="LPO or Invoice Number")

    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True, null=True)

    @property
    def item_total(self):
        """Total goods value before additional costs"""
        return self.quantity * self.unit_price

    @property
    def grand_total(self):
        """Includes transport and handling costs for purchases"""
        if self.trade_type == 'BUY':
            return self.item_total + self.transport_cost + self.labor_cost
        return self.item_total

    def __str__(self):
        return f"{self.date} - {self.get_trade_type_display()}: {self.item_name} ({self.quantity} {self.unit_of_measure})"