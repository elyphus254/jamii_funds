from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import MpesaTransaction
from .serializers import MpesaTransactionSerializer


class MpesaTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MpesaTransaction.objects.all()
    serializer_class = MpesaTransactionSerializer

@api_view(["POST"])
@csrf_exempt
@permission_classes([AllowAny])
def mpesa_callback(request):
    # Simplified callback
    return Response({"status": "received"}, status=status.HTTP_200_OK)