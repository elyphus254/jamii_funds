# daraja/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import MpesaTransaction
import requests
import base64
from datetime import datetime

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_stk_push(request):
    amount = request.data.get('amount')
    phone = request.data.get('phone_number')
    chama_id = request.data.get('chama_id')

    if not all([amount, phone, chama_id]):
        return Response({"error": "amount, phone_number, chama_id required"}, status=400)

    # Create transaction record
    transaction = MpesaTransaction.objects.create(
        user=request.user,
        chama_id=chama_id,
        amount=amount,
        phone_number=phone,
        status='INITIATED'
    )

    # Generate OAuth token
    consumer_key = settings.MPESA['CONSUMER_KEY']
    consumer_secret = settings.MPESA['CONSUMER_SECRET']
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_url, auth=(consumer_key, consumer_secret))
    access_token = r.json()['access_token']

    # STK Push
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f"{settings.MPESA['SHORTCODE']}{settings.MPESA['PASSKEY']}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": settings.MPESA['SHORTCODE'],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone,
        "PartyB": settings.MPESA['SHORTCODE'],
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA['CALLBACK_URL'],
        "AccountReference": f"CH{transaction.id.hex[:8]}",
        "TransactionDesc": "Chama Contribution"
    }

    headers = {'Authorization': f'Bearer {access_token}'}
    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(stk_url, json=payload, headers=headers).json()

    if response.get('ResponseCode') == '0':
        transaction.checkout_request_id = response['CheckoutRequestID']
        transaction.merchant_request_id = response['MerchantRequestID']
        transaction.save()
        return Response({"status": "STK Push sent", "checkout_id": response['CheckoutRequestID']})
    else:
        transaction.mark_as_failed(response.get('errorCode'), response.get('errorMessage'))
        return Response({"error": "STK Push failed"}, status=400)