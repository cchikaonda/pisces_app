from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('cashflow/', views.cashflow_view, name='cashflow'),
    path('trades/', views.trades_view, name='trades'),
    path('reports/', views.reports_view, name='reports'),

    path('invoices/', views.invoices_view, name='invoices'),
    path('invoices/<int:pk>/print/', views.print_invoice_view, name='print_invoice'),
    path('receipts/<int:pk>/print/', views.print_receipt_view, name='print_receipt'),
]