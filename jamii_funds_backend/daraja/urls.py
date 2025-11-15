# daraja/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('stk-push/', views.initiate_stk_push, name='stk_push'),
    path('callback/', views.mpesa_callback, name='callback'),
    path('core/', include('core.urls')),
]