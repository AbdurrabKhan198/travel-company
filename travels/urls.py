from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Public pages
    path('', views.homepage, name='homepage'),
    path('contact/', views.contact, name='contact'),
    path('about/',views.about, name='about'),
    path('test-colors/', TemplateView.as_view(template_name='test_colors.html'), name='test_colors'),
    path('search/', views.search_flights, name='search_flights'),
    
    # Booking
    path('booking/<int:inventory_id>/', views.booking_page, name='booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # User pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    
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
