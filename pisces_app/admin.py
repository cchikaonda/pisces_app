from django.contrib import admin
from django.db.models import Sum
from .models import CashFlow, Trade
from django.contrib import admin
from .models import CashFlow, Trade, Invoice, Payment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'trade', 'issue_date', 'due_date', 'status')
    list_filter = ('status', 'issue_date')
    search_fields = ('invoice_number', 'trade__party_name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'date', 'amount', 'payment_method', 'reference_number')
    list_filter = ('payment_method', 'date')
    search_fields = ('reference_number', 'invoice__invoice_number')

@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'formatted_amount', 'description')
    list_filter = ('transaction_type', 'date')
    search_fields = ('description',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    @admin.display(description='Amount ($)')
    def formatted_amount(self, obj):
        return f"${obj.amount:,.2f}"


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'date', 
        'trade_type', 
        'category', 
        'item_name', 
        'quantity_display', 
        'formatted_unit_price', 
        'party_name', 
        'invoice_ref', 
        'formatted_grand_total'
    )
    list_filter = ('trade_type', 'unit_of_measure', 'category', 'date')
    search_fields = ('item_name', 'category', 'party_name', 'invoice_ref', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)

    # Custom column formatting
    @admin.display(description='Quantity')
    def quantity_display(self, obj):
        return f"{obj.quantity:.2f} {obj.unit_of_measure}"

    @admin.display(description='Unit Price ($)')
    def formatted_unit_price(self, obj):
        return f"${obj.unit_price:,.2f}"

    @admin.display(description='Grand Total ($)')
    def formatted_grand_total(self, obj):
        return f"${obj.grand_total:,.2f}"