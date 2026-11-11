from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('cashflow/', views.cashflow_view, name='cashflow'),
    path('trades/', views.trades_view, name='trades'),
    path('api/items/create/', views.api_create_item, name='api_create_item'),
    path('trades/<int:pk>/edit/', views.trade_update, name='trade_update'),
    path('reports/', views.reports_view, name='reports'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Item & Price URLs
    path('api/item-price/<int:item_id>/', views.get_item_price, name='get_item_price'),
    path('items/', views.item_list, name='item_list'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),

    path('companies/', views.company_list, name='company_list'),
    path('companies/<int:pk>/edit/', views.company_update, name='company_update'),
    path('companies/<int:pk>/delete/', views.company_delete, name='company_delete'),

    path('invoices/', views.invoices_view, name='invoices'),
    path('invoices/<int:pk>/print/', views.print_invoice_view, name='print_invoice'),
    path('receipts/<int:pk>/print/', views.print_receipt_view, name='print_receipt'),
]