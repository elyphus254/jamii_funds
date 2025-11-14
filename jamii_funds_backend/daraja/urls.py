from django.urls import path
from .views import stk_callback

urlpatterns = [
    path('callback/', stk_callback, name='stk_callback'),
]
