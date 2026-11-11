from django.contrib import admin
from django.db.models import Sum
from .models import Company, Item, CashFlow, Trade, TradeItem, Invoice, Payment, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_type', 'phone', 'address')
    list_filter = ('company_type',)
    search_fields = ('name', 'phone', 'address')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'formatted_standard_price', 'unit_of_measure')
    list_filter = ('category', 'unit_of_measure')
    search_fields = ('name', 'category__name')

    @admin.display(description='Standard Price (MK)')
    def formatted_standard_price(self, obj):
        return f"MK {obj.standard_price:,.2f}"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'trade', 'issue_date', 'due_date', 'status')
    list_filter = ('status', 'issue_date')
    search_fields = ('invoice_number', 'trade__company__name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'date', 'formatted_amount', 'payment_method', 'reference_number')
    list_filter = ('payment_method', 'date')
    search_fields = ('reference_number', 'invoice__invoice_number')

    @admin.display(description='Amount (MK)')
    def formatted_amount(self, obj):
        return f"MK {obj.amount:,.2f}"


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'formatted_amount', 'description')
    list_filter = ('transaction_type', 'date')
    search_fields = ('description',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    @admin.display(description='Amount (MK)')
    def formatted_amount(self, obj):
        return f"MK {obj.amount:,.2f}"


class TradeItemInline(admin.TabularInline):
    model = TradeItem
    extra = 1  # Provides 1 empty row by default for adding items
    autocomplete_fields = ['item']  # Optional: makes item selection searchable if you have many items


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    inlines = [TradeItemInline]
    list_display = (
        'date', 
        'trade_type', 
        'company', 
        'items_summary', 
        'invoice_ref', 
        'formatted_other_expenses',
        'formatted_grand_total'
    )
    list_filter = ('trade_type', 'date', 'company')
    search_fields = ('company__name', 'trade_items__item__name', 'invoice_ref', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)

    @admin.display(description='Items')
    def items_summary(self, obj):
        """Displays a summary of items included in this trade."""
        items = obj.trade_items.all()
        if not items:
            return "No items"
        return ", ".join([f"{ti.item.name} ({ti.quantity})" if ti.item else f"Custom ({ti.quantity})" for ti in items])

    @admin.display(description='Other Expenses (MK)')
    def formatted_other_expenses(self, obj):
        return f"MK {obj.other_expenses:,.2f}"

    @admin.display(description='Grand Total (MK)')
    def formatted_grand_total(self, obj):
        return f"MK {obj.grand_total:,.2f}"