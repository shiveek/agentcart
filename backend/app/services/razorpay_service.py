import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import razorpay
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("agentcart.razorpay")


class RazorpayService:
    """Service wrapping Razorpay API calls, HMAC signature verification, and error normalization."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        self._client: Optional[razorpay.Client] = None

    def get_client(self) -> razorpay.Client:
        """Returns initialized Razorpay SDK client or raises safe configuration exception."""
        if not self.key_id or not self.key_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay API credentials are not configured on the server",
            )
        if self._client is None:
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_order(
        self,
        amount_paise: int,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates a Razorpay Order server-side in smallest currency units (e.g. paise)."""
        client = self.get_client()
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }
        try:
            order_data = client.order.create(data=payload)
            return order_data
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment provider error: {str(e)}",
            )

    def fetch_order(self, provider_order_id: str) -> Dict[str, Any]:
        """Fetches Razorpay Order details by provider order ID."""
        client = self.get_client()
        try:
            return client.order.fetch(provider_order_id)
        except Exception as e:
            logger.error(f"Razorpay fetch order failed for '{provider_order_id}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment provider error fetching order: {str(e)}",
            )

    def fetch_payment(self, provider_payment_id: str) -> Dict[str, Any]:
        """Fetches Razorpay Payment details by provider payment ID."""
        client = self.get_client()
        try:
            return client.payment.fetch(provider_payment_id)
        except Exception as e:
            logger.error(f"Razorpay fetch payment failed for '{provider_payment_id}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment provider error fetching payment: {str(e)}",
            )

    def verify_payment_signature(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        signature: str,
    ) -> bool:
        """Verifies checkout HMAC-SHA256 signature using DB-fetched provider_order_id and constant-time comparison."""
        if not self.key_secret:
            raise HTTPException(
                status_code=status.HTTP_533_SERVICE_UNAVAILABLE if hasattr(status, "HTTP_533_SERVICE_UNAVAILABLE") else 503,
                detail="Razorpay Key Secret is missing on the server",
            )

        msg = f"{provider_order_id}|{provider_payment_id}"
        generated_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(generated_signature, signature)

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """Verifies Razorpay Webhook HMAC-SHA256 signature using raw body bytes and constant-time comparison."""
        if not self.webhook_secret:
            logger.warning("RAZORPAY_WEBHOOK_SECRET is not configured on the server")
            return False

        generated_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(generated_signature, signature_header)


razorpay_service = RazorpayService()
