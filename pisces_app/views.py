from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F, FloatField
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from .models import CashFlow, Trade, Invoice, Payment, Category, Item, Company
from .forms import CashFlowForm, TradeForm, InvoiceForm, PaymentForm, CategoryForm, ItemForm, CompanyForm   


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
        'summary': summary,
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


# --- CATEGORY & ITEM CRUD VIEWS ---

@login_required
def category_list(request):
    categories = Category.objects.all()
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added successfully!')
        return redirect('category_list')
    return render(request, 'category_list.html', {'categories': categories, 'form': form})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated successfully!')
        return redirect('category_list')
    return render(request, 'category_form.html', {'form': form, 'category': category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    return render(request, 'category_confirm_delete.html', {'category': category})


@login_required
def item_list(request):
    items = Item.objects.all()
    form = ItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Item added successfully!')
        return redirect('item_list')
    return render(request, 'item_list.html', {'items': items, 'form': form})


@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Item updated successfully!')
        return redirect('item_list')
    return render(request, 'item_form.html', {'form': form, 'item': item})


@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('item_list')
    return render(request, 'item_confirm_delete.html', {'item': item})


# --- COMPANY CRUD VIEWS ---

@login_required
def company_list(request):
    companies = Company.objects.all()
    form = CompanyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Company added successfully!')
        return redirect('company_list')
    return render(request, 'company_list.html', {'companies': companies, 'form': form})


@login_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Company updated successfully!')
        return redirect('company_list')
    return render(request, 'company_form.html', {'form': form, 'company': company})


@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        messages.success(request, 'Company deleted successfully!')
        return redirect('company_list')
    return render(request, 'company_confirm_delete.html', {'company': company})

# --- REPORTS & INVOICING VIEWS ---

@login_required
def reports_view(request):
    period_type = request.GET.get('period', 'monthly')
    
    trunc_func = TruncWeek if period_type == 'weekly' else TruncMonth
    item_total_expr = F('quantity') * F('unit_price')

    trades_qs = Trade.objects.all()
    cashflows_qs = CashFlow.objects.all()

    revenue_report = trades_qs.filter(trade_type='SELL').annotate(
        period=trunc_func('date')
    ).values('period', 'item', 'custom_item_name').annotate(
        total_revenue=Sum(item_total_expr),
        total_qty=Sum('quantity')
    ).order_by('-period')

    purchase_report = trades_qs.filter(trade_type='BUY').annotate(
        period=trunc_func('date')
    ).values('period', 'item', 'custom_item_name', 'company').annotate(
        total_purchases=Sum(item_total_expr),
        total_transport=Sum('transport_cost'),
        total_labor=Sum('labor_cost'),
        total_qty=Sum('quantity')
    ).order_by('-period')

    cashflow_report = cashflows_qs.annotate(
        period=trunc_func('date')
    ).values('period', 'transaction_type').annotate(
        total_amount=Sum('amount')
    ).order_by('-period')

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