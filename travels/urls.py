from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Root URL - shows homepage (visible to everyone)
    path('', views.homepage, name='homepage'),
    # Login page
    path('login/', views.user_login, name='login'),
    # Home page (alias for root)
    path('home/', views.homepage, name='homepage'),
    path('contact/', views.contact, name='contact'),
    path('contact/thanks/<int:contact_id>/', views.contact_thanks, name='contact_thanks'),
    path('about/',views.about, name='about'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('faq/', views.faq, name='faq'),
    path('visit-visa/', views.visit_visa, name='visit_visa'),
    path('apply-visa/', views.apply_visa, name='apply_visa'),
    path('visa-thanks/<str:booking_id>/', views.visa_thanks, name='visa_thanks'),
    path('umrah/', views.umrah, name='umrah'),
    path('umrah/thanks/<int:umrah_id>/', views.umrah_thanks, name='umrah_thanks'),
    path('apply-package/<str:package_name>/', views.apply_package, name='apply_package'),
    path('apply-package/', views.apply_package, name='apply_package'),
    path('test-colors/', TemplateView.as_view(template_name='test_colors.html'), name='test_colors'),
    path('search/', views.search_flights, name='search_flights'),
    
    # Booking
    path('booking/<int:schedule_id>/', views.booking_page, name='booking'),
    path('booking/review/<int:schedule_id>/', views.review_booking, name='review_booking'),
    path('booking/apply-coupon/<int:schedule_id>/', views.apply_coupon, name='apply_coupon'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('booking/<int:booking_id>/fare-rule/', views.fare_rule, name='fare_rule'),
    path('booking/<int:booking_id>/change-request/', views.change_request, name='change_request'),
    path('ticket/<int:booking_id>/view/', views.view_ticket, name='view_ticket'),
    path('ticket/<int:booking_id>/pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    path('ticket/<int:booking_id>/print/', views.print_ticket_pdf, name='print_ticket_pdf'),
    path('ticket/<int:booking_id>/email/', views.email_ticket, name='email_ticket'),
    path('ticket/<int:booking_id>/edit-fare/', views.edit_booking_fare, name='edit_booking_fare'),
    path('ticket/<int:booking_id>/download-without-fare/', views.download_ticket_without_fare, name='download_ticket_without_fare'),
    
    # User pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-trips/', views.my_trips, name='my_trips'),
    # Login path removed - root URL (/) now serves as login page
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # OTP Verification
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    path('api/send-ticket-email/', views.send_ticket_email_api, name='send_ticket_email_api'),
    path('ticket/<int:booking_id>/pdf/download/', views.download_ticket_pdf_file, name='download_ticket_pdf_file'),
    
    # Wallet
    path('wallet/recharge/', views.wallet_recharge, name='wallet_recharge'),
    path('wallet/history/', views.wallet_history, name='wallet_history'),
    
    # Group Request (B2B)
    path('group-request/', views.group_request, name='group_request'),
    path('group-request/thanks/<int:request_id>/', views.group_request_thanks, name='group_request_thanks'),
    
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
