from decimal import Decimal
from .models import ODWallet, CashBalanceWallet, SalesRepresentative

def wallet_context(request):
    """Context processor to add wallet information and sales representatives to all templates"""
    context = {
        'cash_balance': Decimal('0'),
        'has_cash_balance_wallet': False,
        'od_wallet_balance': Decimal('0'),
        'has_od_wallet': False,
        'has_od_wallet_access': False,
        'sales_representatives': [],
    }
    
    # Get sales representatives for header - show only assigned rep if user is logged in
    try:
        user = request.user
        if user.is_authenticated:
            # Try to get profile - some users might have profile through signals
            profile = getattr(user, 'profile', None)
            if profile and profile.sales_representative:
                # Show the assigned sales representative even if not globally active
                # as it was explicitly assigned to this user/agency
                sales_reps = [profile.sales_representative]
                context['sales_representatives'] = sales_reps
            else:
                # If no specific rep assigned, show all active ones
                sales_reps = SalesRepresentative.objects.filter(is_active=True).order_by('display_order', 'name')
                context['sales_representatives'] = sales_reps
        else:
            # For non-authenticated users, show all active ones
            sales_reps = SalesRepresentative.objects.filter(is_active=True).order_by('display_order', 'name')
            context['sales_representatives'] = sales_reps
    except Exception as e:
        # For development debugging
        if settings.DEBUG:
            print(f"Error in sales_reps context processor: {e}")
        pass
    
    if request.user.is_authenticated:
        # Get Cash Balance Wallet (auto-create if doesn't exist)
        try:
            cash_balance_wallet = CashBalanceWallet.objects.get(user=request.user)
            context['cash_balance'] = cash_balance_wallet.balance
            context['has_cash_balance_wallet'] = True
        except CashBalanceWallet.DoesNotExist:
            # Auto-create cash balance wallet for authenticated users
            try:
                cash_balance_wallet = CashBalanceWallet.objects.create(user=request.user)
                context['cash_balance'] = Decimal('0')
                context['has_cash_balance_wallet'] = True
            except Exception:
                # If creation fails, just use defaults
                pass
        
        # Get OD Wallet (only if exists and active)
        try:
            od_wallet = ODWallet.objects.get(user=request.user)
            context['od_wallet_balance'] = od_wallet.balance
            context['has_od_wallet'] = True
            context['has_od_wallet_access'] = od_wallet.is_active and not od_wallet.is_expired()
            context['od_wallet_days_remaining'] = od_wallet.days_remaining()
            context['od_wallet_is_expired'] = od_wallet.is_expired()
        except ODWallet.DoesNotExist:
            pass
    
    return context

