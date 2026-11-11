from django import forms
from .models import Company, Item, CashFlow, Trade, Invoice, Payment, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm', 'placeholder': 'e.g., Vegetables, Produce'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm', 'placeholder': 'Optional description'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'company_type', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm', 'placeholder': 'e.g., Chipiku Plus City Centre'}),
            'company_type': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'standard_price', 'unit_of_measure']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm', 'placeholder': 'e.g., Irish Potatoes'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'standard_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'unit_of_measure': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
        }


class CashFlowForm(forms.ModelForm):
    class Meta:
        model = CashFlow
        fields = ['date', 'transaction_type', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'transaction_type': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'description': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm', 'placeholder': 'Note or description'}),
        }


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            'date',
            'trade_type',
            'company',
            'invoice_ref',
            'transport_cost',
            'labor_cost',
            'other_expenses',
            'description'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'trade_type': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'company': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'invoice_ref': forms.TextInput(attrs={'placeholder': 'e.g. LPO-001', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'transport_cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'labor_cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'other_expenses': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
            'description': forms.TextInput(attrs={'placeholder': 'Optional notes', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['trade', 'due_date', 'status', 'notes'] # Removed 'invoice_number'
        widgets = {
            'trade': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'date', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'reference_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'notes': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
        }