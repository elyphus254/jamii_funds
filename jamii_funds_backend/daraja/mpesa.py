# daraja/mpesa.py
"""
M-Pesa Daraja API helpers (STK Push, C2B, etc.)
Uses sandbox by default – switch to production via settings.
"""
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from django.conf import settings
from django.utils import timezone

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SANDBOX_BASE = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE = "https://api.safaricom.co.ke"

# ----------------------------------------------------------------------
# Helper: Get OAuth token
# ----------------------------------------------------------------------
def _get_access_token() -> str:
    """
    Fetch M-Pesa OAuth access token.
    Raises RuntimeError on failure.
    """
    cfg = settings.MPESA
    env = cfg.get("ENV", "sandbox").lower()
    base_url = SANDBOX_BASE if env == "sandbox" else PRODUCTION_BASE

    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    auth = (cfg["CONSUMER_KEY"], cfg["CONSUMER_SECRET"])

    try:
        response = requests.get(url, auth=auth, timeout=10)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("Access token missing in response")
        logger.info("M-Pesa access token obtained")
        return token
    except requests.RequestException as e:
        logger.error(f"M-Pesa OAuth failed: {e}")
        raise RuntimeError("Failed to get M-Pesa access token") from e


# ----------------------------------------------------------------------
# STK Push
# ----------------------------------------------------------------------
def stk_push(
    phone_number: str,
    amount: float,
    account_reference: str,
    description: str,
    *,
    transaction_type: str = "CONTRIBUTION",
    chama_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Initiate STK Push.
    Returns raw M-Pesa response.
    Optionally creates MpesaTransaction record.
    """
    cfg = settings.MPESA
    env = cfg.get("ENV", "sandbox").lower()
    base_url = SANDBOX_BASE if env == "sandbox" else PRODUCTION_BASE

    # ------------------------------------------------------------------
    # 1. Create transaction record (optional but recommended)
    # ------------------------------------------------------------------
    from .models import MpesaTransaction
    transaction = MpesaTransaction.objects.create(
        user_id=user_id,
        chama_id=chama_id,
        amount=amount,
        phone_number=phone_number,
        transaction_type=transaction_type,
        status="INITIATED",
    )

    # ------------------------------------------------------------------
    # 2. Build STK Push payload
    # ------------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{cfg['SHORTCODE']}{cfg['PASSKEY']}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode()

    payload = {
        "BusinessShortCode": cfg["SHORTCODE"],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),  # M-Pesa expects integer
        "PartyA": phone_number,
        "PartyB": cfg["SHORTCODE"],
        "PhoneNumber": phone_number,
        "CallBackURL": cfg["CALLBACK_URL"],
        "AccountReference": account_reference[:12],  # max 12 chars
        "TransactionDesc": description[:100],
    }

    headers = {"Authorization": f"Bearer {_get_access_token()}"}
    url = f"{base_url}/mpesa/stkpush/v1/processrequest"

    # ------------------------------------------------------------------
    # 3. Send request
    # ------------------------------------------------------------------
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.info(f"STK Push initiated: {data.get('CheckoutRequestID')}")

        # Update transaction with M-Pesa IDs
        transaction.merchant_request_id = data.get("MerchantRequestID")
        transaction.checkout_request_id = data.get("CheckoutRequestID")
        transaction.save()

        return data

    except requests.RequestException as e:
        logger.error(f"STK Push failed: {e}")
        transaction.mark_as_failed("REQUEST_ERROR", str(e))
        raise RuntimeError("STK Push failed") from e