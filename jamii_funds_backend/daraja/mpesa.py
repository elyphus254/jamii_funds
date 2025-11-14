import requests, base64, datetime

def get_access_token(consumer_key, consumer_secret):
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=(consumer_key, consumer_secret))
    return r.json().get('access_token')

def stk_push(phone_number, amount, account_reference, description):
    access_token = get_access_token("YOUR_CONSUMER_KEY", "YOUR_CONSUMER_SECRET")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    business_short_code = "174379"
    password = base64.b64encode((business_short_code + "YOUR_PASSKEY" + timestamp).encode()).decode("utf-8")

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": business_short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://yourdomain.com/api/daraja/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": description
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json()
