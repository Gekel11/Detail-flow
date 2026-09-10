from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('order/new/', views.order_create_view, name='order_create'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('order/<int:order_id>/certificate/', views.download_certificate_pdf_view, name='order_certificate_pdf'),
    path('order/<int:order_id>/mark-ready/', views.mark_order_ready_view, name='mark_order_ready'),
    path('order/<int:order_id>/status/<str:new_status>/', views.order_update_status_view, name='order_update_status'),
    path('vehicle/new/', views.vehicle_create_view, name='vehicle_create'),
    path('customer/new/', views.customer_create_view, name='customer_create'),
]