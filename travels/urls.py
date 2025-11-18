from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Public pages
    path('', views.homepage, name='homepage'),
    path('contact/', views.contact, name='contact'),
    path('contact/thanks/<int:contact_id>/', views.contact_thanks, name='contact_thanks'),
    path('about/',views.about, name='about'),
    path('test-colors/', TemplateView.as_view(template_name='test_colors.html'), name='test_colors'),
    path('search/', views.search_flights, name='search_flights'),
    
    # Booking
    path('booking/<int:schedule_id>/', views.booking_page, name='booking'),
    path('booking/review/<int:schedule_id>/', views.review_booking, name='review_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('ticket/<int:booking_id>/pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    path('ticket/<int:booking_id>/print/', views.print_ticket_pdf, name='print_ticket_pdf'),
    path('ticket/<int:booking_id>/email/', views.email_ticket, name='email_ticket'),
    path('ticket/<int:booking_id>/edit-fare/', views.edit_booking_fare, name='edit_booking_fare'),
    
    # User pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    
    # OTP Verification
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Wallet
    path('wallet/recharge/', views.wallet_recharge, name='wallet_recharge'),
    path('wallet/history/', views.wallet_history, name='wallet_history'),
    
    # Profile PDF Management
    path('profile/pdf/upload/', views.upload_profile_pdf, name='upload_profile_pdf'),
    path('profile/pdf/delete/', views.delete_profile_pdf, name='delete_profile_pdf'),
    
    # Admin pages - Schedules
    path('admin/schedules/', views.admin_schedules, name='admin_schedules'),
    path('admin/schedules/add/', views.add_schedule, name='add_schedule'),
    path('admin/schedules/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('admin/packages/', views.admin_packages, name='admin_packages'),
    path('admin/packages/add/', views.add_package, name='add_package'),
    path('admin/packages/delete/<int:package_id>/', views.delete_package, name='delete_package'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
