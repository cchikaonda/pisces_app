from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F, FloatField
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from .models import CashFlow, Trade
from .forms import CashFlowForm, TradeForm


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

    context = {
        'cash_balance': current_balance,
        'sales': trade_totals['sales'],
        'expenses': total_expenses,
        'net_profit': net_profit,
        'recent_cashflows': cashflows.order_by('-date')[:5],
        'recent_trades': trades.order_by('-date')[:5],
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
    
    # Use database-level grouping via TruncWeek or TruncMonth
    trunc_func = TruncWeek if period_type == 'weekly' else TruncMonth
    item_total_expr = F('quantity') * F('unit_price')

    report_qs = Trade.objects.annotate(period=trunc_func('date')).values('period').annotate(
        revenue=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost'), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost'), 0.0, output_field=FloatField())
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

    return render(request, 'reports.html', {'summary': summary, 'period_type': period_type})