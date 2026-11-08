from django import forms
from .models import CashFlow, Trade
from django import forms
from .models import CashFlow, Trade, Invoice, Payment

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['trade', 'invoice_number', 'issue_date', 'due_date', 'status', 'notes']
        widgets = {
            'trade': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'invoice_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm'}),
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

class CashFlowForm(forms.ModelForm):
    class Meta:
        model = CashFlow
        fields = ['date', 'transaction_type', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Note or description'}),
        }

from django import forms
from .models import Trade

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            'trade_type', 
            'company', 
            'item', 
            'custom_item_name', 
            'quantity', 
            'unit_price', 
            'invoice_ref', 
            'transport_cost', 
            'labor_cost', 
            'description'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }