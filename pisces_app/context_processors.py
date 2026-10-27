from django.conf import settings

def currency_context(request):
    return {
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', '$')
    }