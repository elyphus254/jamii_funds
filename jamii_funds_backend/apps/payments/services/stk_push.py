# apps/payments/services/stk_push.py
import requests
import base64
import datetime
from django.conf import settings


def get_access_token():
    """Get OAuth token from M-Pesa"""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    auth_str = f"{consumer_key}:{consumer_secret}"
    auth_token = base64.b64encode(auth_str.encode()).decode()

    headers = {"Authorization": f"Basic {auth_token}"}
    response = requests.get(api_url, headers=headers)
    return response.json().get("access_token")


def initiate_stk_push(phone, amount, account_ref, callback_url):
    """
    Initiate STK Push
    Docs: https://developer.safaricom.co.ke/APIs/STKPush
    """
    access_token = get_access_token()
    if not access_token:
        return {"ResponseCode": "1", "error": "Failed to get token"}

    # Format phone: remove leading 0, add 254
    phone = phone.lstrip("0")
    if not phone.startswith("254"):
        phone = "254" + phone

    # Generate password
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = shortcode + passkey + timestamp
    encoded_password = base64.b64encode(data_to_encode.encode()).decode()

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "BusinessShortCode": shortcode,
        "Password": encoded_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(int(amount)),
        "PartyA": phone * 1,
        "PartyB": shortcode,
        "PhoneNumber": phone * 1,
        "CallBackURL": callback_url,
        "AccountReference": account_ref,
        "TransactionDesc": f"Contribution to {account_ref}",
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()