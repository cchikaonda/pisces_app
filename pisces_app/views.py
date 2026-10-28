from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F, FloatField
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from .models import CashFlow, Trade
from .forms import CashFlowForm, TradeForm
from .models import Invoice, Payment
from .forms import InvoiceForm, PaymentForm  # Make sure to create these forms in forms.py


@login_required
def dashboard(request):
    cashflows = CashFlow.objects.all()
    trades = Trade.objects.all()

    # Aggregate CashFlow values in database
    cf_totals = cashflows.aggregate(
        capital=Coalesce(Sum('amount', filter=Q(transaction_type='Capital Input')), 0.0, output_field=FloatField()),
        deposits=Coalesce(Sum('amount', filter=Q(transaction_type='Deposit')), 0.0, output_field=FloatField()),
        withdrawals=Coalesce(Sum('amount', filter=Q(transaction_type='Withdrawal')), 0.0, output_field=FloatField())
    )

    # Calculate item_total dynamically in SQL (quantity * unit_price)
    item_total_expr = F('quantity') * F('unit_price')

    trade_totals = trades.aggregate(
        sales=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost'), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost'), 0.0, output_field=FloatField())
    )

    total_expenses = trade_totals['purchases'] + trade_totals['transport'] + trade_totals['labor']
    net_profit = trade_totals['sales'] - total_expenses
    current_balance = (cf_totals['capital'] + cf_totals['deposits'] + trade_totals['sales']) - (cf_totals['withdrawals'] + total_expenses)

    # Generate P&L monthly summary for the dashboard table
    report_qs = Trade.objects.annotate(period=TruncMonth('date')).values('period').annotate(
        revenue=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost'), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost'), 0.0, output_field=FloatField())
    ).order_by('-period')

    summary = []
    for row in report_qs:
        total_exp = row['purchases'] + row['transport'] + row['labor']
        summary.append({
            'period': row['period'].strftime('%Y-%m') if row['period'] else 'N/A',
            'revenue': row['revenue'],
            'purchases': row['purchases'],
            'transport': row['transport'],
            'labor': row['labor'],
            'total_expenses': total_exp,
            'net_profit': row['revenue'] - total_exp
        })

    context = {
        'cash_balance': current_balance,
        'sales': trade_totals['sales'],
        'expenses': total_expenses,
        'net_profit': net_profit,
        'recent_cashflows': cashflows.order_by('-date')[:5],
        'recent_trades': trades.order_by('-date')[:5],
        'summary': summary,  # Included P&L summary for dashboard
    }
    return render(request, 'dashboard.html', context)

@login_required
def cashflow_view(request):
    if request.method == 'POST':
        form = CashFlowForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cashflow entry successfully recorded!')
            return redirect('cashflow')
        else:
            messages.error(request, 'Failed to record transaction. Please check inputs.')
    else:
        form = CashFlowForm()

    records = CashFlow.objects.all().order_by('-date')
    return render(request, 'cashflow.html', {'form': form, 'records': records})


@login_required
def trades_view(request):
    if request.method == 'POST':
        form = TradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trade transaction saved successfully!')
            return redirect('trades')
        else:
            messages.error(request, 'Failed to record trade. Please check form inputs.')
    else:
        form = TradeForm()

    records = Trade.objects.all().order_by('-date')
    return render(request, 'trades.html', {'form': form, 'records': records})


@login_required
def reports_view(request):
    period_type = request.GET.get('period', 'monthly')
    selected_category = request.GET.get('category', '')
    
    trunc_func = TruncWeek if period_type == 'weekly' else TruncMonth
    item_total_expr = F('quantity') * F('unit_price')

    trades_qs = Trade.objects.all()
    cashflows_qs = CashFlow.objects.all()
    if selected_category:
        trades_qs = trades_qs.filter(category=selected_category)

    # 1. Revenue (Sales) Report Grouping
    revenue_report = trades_qs.filter(trade_type='SELL').annotate(
        period=trunc_func('date')
    ).values('period', 'category', 'item_name').annotate(
        total_revenue=Sum(item_total_expr),
        total_qty=Sum('quantity')
    ).order_by('-period')

    # 2. Purchase Report Grouping
    purchase_report = trades_qs.filter(trade_type='BUY').annotate(
        period=trunc_func('date')
    ).values('period', 'category', 'item_name', 'party_name').annotate(
        total_purchases=Sum(item_total_expr),
        total_transport=Sum('transport_cost'),
        total_labor=Sum('labor_cost'),
        total_qty=Sum('quantity')
    ).order_by('-period')

    # 3. Cash Flow Report Grouping
    cashflow_report = cashflows_qs.annotate(
        period=trunc_func('date')
    ).values('period', 'transaction_type').annotate(
        total_amount=Sum('amount')
    ).order_by('-period')

    # 4. Overall P&L Summary (Existing)
    report_qs = trades_qs.annotate(period=trunc_func('date')).values('period').annotate(
        revenue=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost', filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost', filter=Q(trade_type='BUY')), 0.0, output_field=FloatField())
    ).order_by('-period')

    summary = []
    for row in report_qs:
        total_exp = row['purchases'] + row['transport'] + row['labor']
        date_format = '%Y-W%U' if period_type == 'weekly' else '%Y-%m'
        summary.append({
            'period': row['period'].strftime(date_format) if row['period'] else 'N/A',
            'revenue': row['revenue'],
            'purchases': row['purchases'],
            'transport': row['transport'],
            'labor': row['labor'],
            'total_expenses': total_exp,
            'net_profit': row['revenue'] - total_exp
        })

    context = {
        'summary': summary,
        'revenue_report': revenue_report,
        'purchase_report': purchase_report,
        'cashflow_report': cashflow_report,
        'period_type': period_type,
        'selected_category': selected_category,
        'all_categories': Trade.objects.values_list('category', flat=True).distinct(),
    }
    return render(request, 'reports.html', context)

@login_required
def invoices_view(request):
    invoices = Invoice.objects.all().order_by('-issue_date')
    payments = Payment.objects.all().order_by('-date')

    form = InvoiceForm(request.POST or None, prefix='invoice')
    payment_form = PaymentForm(request.POST or None, prefix='payment')

    if request.method == 'POST':
        if 'invoice_submit' in request.POST and form.is_valid():
            form.save()
            messages.success(request, 'Invoice generated successfully!')
            return redirect('invoices')
            
        elif 'payment_submit' in request.POST and payment_form.is_valid():
            payment = payment_form.save()
            
            # Automatically update invoice status based on total payments
            invoice = payment.invoice
            if invoice and invoice.trade:
                total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
                grand_total = invoice.trade.grand_total

                if total_paid >= grand_total:
                    invoice.status = 'Paid'
                elif total_paid > 0:
                    invoice.status = 'Partial'
                else:
                    invoice.status = 'Sent'
                invoice.save()

            messages.success(request, 'Payment recorded and invoice status updated successfully!')
            return redirect('invoices')

    context = {
        'invoices': invoices,
        'payments': payments,
        'form': InvoiceForm(prefix='invoice'),
        'payment_form': PaymentForm(prefix='payment'),
    }
    return render(request, 'invoices.html', context)

@login_required
def print_invoice_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
    balance_due = invoice.trade.grand_total - total_paid
    
    context = {
        'invoice': invoice,
        'total_paid': total_paid,
        'balance_due': balance_due,
    }
    return render(request, 'print_invoice.html', context)


@login_required
def print_receipt_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'payment': payment,
    }
    return render(request, 'print_receipt.html', context)