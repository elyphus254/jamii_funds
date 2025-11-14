from django.urls import path
from django.http import JsonResponse

def mpesa_callback(request):
    return JsonResponse({'message': 'M-Pesa endpoint working!'})

urlpatterns = [
    path('callback/', mpesa_callback, name='mpesa-callback'),
]
