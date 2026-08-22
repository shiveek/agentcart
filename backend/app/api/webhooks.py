from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.payment import WebhookResponse
from app.services import payment_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/razorpay",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Razorpay Webhook Event",
    description=(
        "Receives raw body Razorpay webhook events, verifies X-Razorpay-Signature HMAC against RAZORPAY_WEBHOOK_SECRET, "
        "enforces replay protection / idempotency via the WebhookEvent table, and updates Payment/Order states."
    ),
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
) -> WebhookResponse:
    """Razorpay Webhook endpoint."""
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header",
        )

    raw_body = await request.body()
    return payment_service.process_webhook_event(
        db=db,
        raw_body=raw_body,
        signature_header=x_razorpay_signature,
    )
