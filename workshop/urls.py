from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('order/new/', views.order_create_view, name='order_create'),
    path('order/<int:order_id>/mark-ready/', views.mark_order_ready_view, name='mark_order_ready'),
]