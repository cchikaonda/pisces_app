from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F, FloatField
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from .models import CashFlow, Trade, TradeItem, Invoice, Payment, Category, Item, Company  # <--- Added TradeItem here
from .forms import CashFlowForm, TradeForm, InvoiceForm, PaymentForm, CategoryForm, ItemForm, CompanyForm   
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
def dashboard(request):
    cashflows = CashFlow.objects.all()
    # Prefetch trade_items and related item details to avoid N+1 queries and make them accessible in templates
    trades = Trade.objects.prefetch_related('trade_items__item').all()

    # Aggregate CashFlow values in database
    cf_totals = cashflows.aggregate(
        capital=Coalesce(Sum('amount', filter=Q(transaction_type='Capital Input')), 0.0, output_field=FloatField()),
        deposits=Coalesce(Sum('amount', filter=Q(transaction_type='Deposit')), 0.0, output_field=FloatField()),
        withdrawals=Coalesce(Sum('amount', filter=Q(transaction_type='Withdrawal')), 0.0, output_field=FloatField())
    )

    # Calculate item_total dynamically through trade_items (quantity * unit_price)
    item_total_expr = F('trade_items__quantity') * F('trade_items__unit_price')

    trade_totals = trades.aggregate(
        sales=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost'), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost'), 0.0, output_field=FloatField()),
        other_expenses=Coalesce(Sum('other_expenses'), 0.0, output_field=FloatField())
    )

    total_expenses = trade_totals['purchases'] + trade_totals['transport'] + trade_totals['labor'] + trade_totals['other_expenses']
    net_profit = trade_totals['sales'] - total_expenses
    current_balance = (cf_totals['capital'] + cf_totals['deposits'] + trade_totals['sales']) - (cf_totals['withdrawals'] + total_expenses)

    # Generate P&L monthly summary for the dashboard table using trade_items
    report_qs = Trade.objects.annotate(period=TruncMonth('date')).values('period').annotate(
        revenue=Coalesce(Sum(item_total_expr, filter=Q(trade_type='SELL')), 0.0, output_field=FloatField()),
        purchases=Coalesce(Sum(item_total_expr, filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        transport=Coalesce(Sum('transport_cost'), 0.0, output_field=FloatField()),
        labor=Coalesce(Sum('labor_cost'), 0.0, output_field=FloatField()),
        other_expenses=Coalesce(Sum('other_expenses'), 0.0, output_field=FloatField())
    ).order_by('-period')

    summary = []
    for row in report_qs:
        total_exp = row['purchases'] + row['transport'] + row['labor'] + row['other_expenses']
        summary.append({
            'period': row['period'].strftime('%Y-%m') if row['period'] else 'N/A',
            'revenue': row['revenue'],
            'purchases': row['purchases'],
            'transport': row['transport'],
            'labor': row['labor'],
            'other_expenses': row['other_expenses'],
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
def get_item_price(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
        return JsonResponse({'success': True, 'standard_price': float(item.standard_price)})
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'standard_price': 0.00})


@login_required
def trades_view(request):
    all_items = Item.objects.all()
    all_categories = Category.objects.all()

    # Capture filter parameters from GET request
    selected_category = request.GET.get('category', '').strip()
    selected_item = request.GET.get('item', '').strip()

    records = Trade.objects.all().order_by('-date')

    # Apply filters if selected
    if selected_category:
        records = records.filter(trade_items__item__category__name__iexact=selected_category)
    if selected_item:
        records = records.filter(trade_items__item__pk=selected_item)

    # Remove duplicates if a trade matches multiple filters
    records = records.distinct()

    if request.method == 'POST':
        form = TradeForm(request.POST)
        items = request.POST.getlist('item[]')
        quantities = request.POST.getlist('quantity[]')
        unit_prices = request.POST.getlist('unit_price[]')

        if form.is_valid() and items and any(items):
            trade = form.save()  # Saves parent Trade instance
            
            for i in range(len(items)):
                if not items[i] or not quantities[i]:
                    continue
                
                TradeItem.objects.create(
                    trade=trade,
                    item_id=items[i],
                    quantity=float(quantities[i]),
                    unit_price=float(unit_prices[i] or 0)
                )

            messages.success(request, 'Trade transaction saved successfully!')
            return redirect('trades')
        else:
            messages.error(request, 'Please check form inputs and ensure at least one item is selected.')
    else:
        form = TradeForm()

    context = {
        'form': form,
        'records': records,
        'all_items': all_items,
        'all_categories': all_categories,
        'selected_category': selected_category,
        'selected_item': selected_item,
    }
    return render(request, 'trades.html', context)

@require_POST
def api_create_item(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        category_name = data.get('category', '').strip()
        unit_of_measure = data.get('unit_of_measure', '')
        standard_price = data.get('standard_price', 0)

        if not name or not category_name:
            return JsonResponse({'success': False, 'error': 'Name and Category are required.'}, status=400)

        # Retrieve the Category instance based on the selected name/string
        category_obj = Category.objects.filter(name__iexact=category_name).first()
        
        if not category_obj:
            return JsonResponse({'success': False, 'error': 'Selected category does not exist.'}, status=400)

        item = Item.objects.create(
            name=name,
            category=category_obj,  # Pass the Category model instance
            unit_of_measure=unit_of_measure,
            standard_price=standard_price or 0
        )

        return JsonResponse({
            'success': True,
            'item': {
                'id': item.pk,
                'name': item.name,
                'unit_of_measure': item.unit_of_measure,
                'standard_price': float(item.standard_price)
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def trade_update(request, pk):
    trade = get_object_or_404(Trade, pk=pk)
    form = TradeForm(request.POST or None, instance=trade)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Transaction updated successfully!')
        return redirect('trades')
    
    records = Trade.objects.all().order_by('-date')
    context = {
        'form': form,
        'records': records,
        'is_edit': True,
        'edit_trade': trade
    }
    return render(request, 'trades.html', context)


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
    selected_category = request.GET.get('category', '')
    
    trunc_func = TruncWeek if period_type == 'weekly' else TruncMonth
    item_total_expr = F('trade_items__quantity') * F('trade_items__unit_price')

    trades_qs = Trade.objects.all()
    cashflows_qs = CashFlow.objects.all()

    if selected_category:
        trades_qs = trades_qs.filter(trade_items__item__category__name=selected_category)

    revenue_report = trades_qs.filter(trade_type='SELL').annotate(
        period=trunc_func('date')
    ).values(
        'period', 
        item_name=F('trade_items__item__name'), 
        category_name=F('trade_items__item__category__name'),
        unit_of_measure=F('trade_items__item__unit_of_measure')
    ).annotate(
        total_revenue=Sum(item_total_expr),
        total_qty=Sum('trade_items__quantity')
    ).order_by('-period')

    purchase_report = trades_qs.filter(trade_type='BUY').annotate(
        period=trunc_func('date')
    ).values(
        'period', 
        item_name=F('trade_items__item__name'), 
        category_name=F('trade_items__item__category__name'), 
        supplier_name=F('company__name'),
        unit_of_measure=F('trade_items__item__unit_of_measure')
    ).annotate(
        total_purchases=Sum(item_total_expr),
        total_transport=Sum('transport_cost'),
        total_labor=Sum('labor_cost'),
        total_other_expenses=Sum('other_expenses'),
        total_qty=Sum('trade_items__quantity')
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
        labor=Coalesce(Sum('labor_cost', filter=Q(trade_type='BUY')), 0.0, output_field=FloatField()),
        other_expenses=Coalesce(Sum('other_expenses', filter=Q(trade_type='BUY')), 0.0, output_field=FloatField())
    ).order_by('-period')

    summary = []
    for row in report_qs:
        total_exp = row['purchases'] + row['transport'] + row['labor'] + row['other_expenses']
        date_format = '%Y-W%U' if period_type == 'weekly' else '%Y-%m'
        summary.append({
            'period': row['period'].strftime(date_format) if row['period'] else 'N/A',
            'revenue': row['revenue'],
            'purchases': row['purchases'],
            'transport': row['transport'],
            'labor': row['labor'],
            'other_expenses': row['other_expenses'],
            'total_expenses': total_exp,
            'net_profit': row['revenue'] - total_exp
        })

    all_categories = Category.objects.values_list('name', flat=True).distinct()

    context = {
        'summary': summary,
        'revenue_report': revenue_report,
        'purchase_report': purchase_report,
        'cashflow_report': cashflow_report,
        'period_type': period_type,
        'all_categories': all_categories,
        'selected_category': selected_category,
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
                # Calculate total paid across all receipts tied to this invoice
                total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
                grand_total = invoice.trade.grand_total

                # Automatically switch status based on amount covered
                if total_paid >= grand_total:
                    invoice.status = 'Paid'        # Displays as "Full Payment"
                elif total_paid > 0:
                    invoice.status = 'Partial'     # Displays as "Partial Payment"
                else:
                    invoice.status = 'Sent'
                    
                invoice.save(update_fields=['status'])

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
    
    trade_total = getattr(invoice.trade, 'grand_total', None)
    if trade_total is None:
        trade_total = getattr(invoice, 'amount', 0) or 0
        
    balance_due = trade_total - total_paid
    
    # Use 'trade_items' because that is the related_name in your TradeItem model
    trade_items = invoice.trade.trade_items.all() if invoice.trade else []

    context = {
        'invoice': invoice,
        'total_paid': total_paid,
        'balance_due': balance_due,
        'trade_items': trade_items,
    }
    return render(request, 'print_invoice.html', context)

@login_required
def print_receipt_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    context = {
        'payment': payment,
    }
    return render(request, 'print_receipt.html', context)