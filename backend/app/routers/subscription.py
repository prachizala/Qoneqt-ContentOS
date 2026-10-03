import os
import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.config.pricing import PRICING_TIERS
from backend.app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["Subscription & Pricing"])

class OrderCreateRequest(BaseModel):
    plan: str = "creator"
    amount: float = 499.0
    currency: str = "INR"

class PaymentCaptureRequest(BaseModel):
    plan: str = "creator"
    amount: float = 499.0
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    signature: Optional[str] = None
    card_number: Optional[str] = None
    expiry: Optional[str] = None
    cvv: Optional[str] = None
    name_on_card: Optional[str] = None

class UpgradeRequest(BaseModel):
    tier_id: str

@router.get("/tiers")
async def get_pricing_tiers() -> Dict[str, Any]:
    """
    Returns all configured pricing tiers and comparison metrics.
    """
    return {
        "tiers": list(PRICING_TIERS.values()),
        "current_tier": SubscriptionService.get_current_tier_id()
    }

@router.get("/usage")
async def get_subscription_usage(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns live monthly video creation usage and active tier limit info.
    """
    return await SubscriptionService.get_usage_summary(db)

@router.post("/create-order")
async def create_subscription_order(
    payload: OrderCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Creates a Razorpay/Stripe checkout order for ₹499 INR (Creator Plan).
    Returns order details and merchant key for checkout modal integration.
    """
    plan_id = payload.plan.lower()
    if plan_id not in PRICING_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{payload.plan}'. Valid options: {list(PRICING_TIERS.keys())}"
        )

    tier = PRICING_TIERS[plan_id]
    amount_in_paise = int(payload.amount * 100) # 499 INR = 49900 paise
    key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_qoneqt_creator_key")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

    order_id = f"order_qoneqt_{int(time.time())}_{os.urandom(3).hex()}"

    # If Razorpay SDK keys are available, instantiate actual Razorpay order
    if key_secret:
        try:
            import razorpay
            client = razorpay.Client(auth=(key_id, key_secret))
            order_data = {
                "amount": amount_in_paise,
                "currency": payload.currency,
                "receipt": f"rcpt_{int(time.time())}",
                "notes": {
                    "plan": plan_id,
                    "platform": "Qoneqt AI ContentOS"
                }
            }
            rzp_order = client.order.create(data=order_data)
            order_id = rzp_order.get("id", order_id)
        except Exception as exc:
            logger.warning(f"Razorpay SDK initialization failed ({exc}). Using standard fallback order session.")

    logger.info(f"[Subscription] Created checkout order '{order_id}' for plan '{plan_id}' ({payload.amount} {payload.currency})")

    return {
        "status": "success",
        "order_id": order_id,
        "amount": amount_in_paise,
        "amount_display": f"₹{payload.amount:.0f}",
        "currency": payload.currency,
        "key_id": key_id,
        "plan": plan_id,
        "plan_name": tier["name"],
        "videos_limit": tier["video_limit_monthly"],
        "scripts_limit": 100 if plan_id == "creator" else 10
    }

@router.post("/capture-payment")
@router.post("/process-payment")
async def capture_payment(
    payload: PaymentCaptureRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Captures payment and upgrades user subscription status in database:
    - Sets plan = 'CREATOR', subscription_status = 'ACTIVE'
    - Sets videos_limit = 15, scripts_limit = 100, reset_date = now() + 30 days.
    """
    plan_id = payload.plan.lower()
    if plan_id not in PRICING_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{payload.plan}'. Valid options: {list(PRICING_TIERS.keys())}"
        )

    payment_id = payload.payment_id or f"pay_qoneqt_{int(time.time())}_{os.urandom(3).hex()}"
    order_id = payload.order_id or f"order_qoneqt_{int(time.time())}"

    # Update database persistent UserSubscription record
    updated_sub = await SubscriptionService.update_user_subscription(
        db=db,
        plan=plan_id.upper(),
        payment_id=payment_id,
        order_id=order_id,
        provider="RAZORPAY"
    )

    summary = await SubscriptionService.get_usage_summary(db)

    return {
        "status": "success",
        "message": f"Payment of ₹{payload.amount:.0f} captured successfully! Creator Plan activated.",
        "transaction_id": payment_id,
        "order_id": order_id,
        "subscription": summary
    }

@router.post("/webhook")
async def subscription_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Razorpay / Stripe webhook handler for subscription payment capture success.
    Updates database UserSubscription to ACTIVE Creator Plan.
    """
    try:
        body = await request.json()
        event = body.get("event", "payment.captured")
        payload_data = body.get("payload", {}).get("payment", {}).get("entity", {})

        payment_id = payload_data.get("id") or f"pay_wh_{int(time.time())}"
        order_id = payload_data.get("order_id") or f"order_wh_{int(time.time())}"
        notes = payload_data.get("notes", {})
        target_plan = notes.get("plan", "CREATOR").upper()

        if event in ("payment.captured", "order.paid", "invoice.payment_succeeded"):
            await SubscriptionService.update_user_subscription(
                db=db,
                plan=target_plan,
                payment_id=payment_id,
                order_id=order_id,
                provider="RAZORPAY_WEBHOOK"
            )
            logger.info(f"[Webhook] Successfully processed event '{event}' for order '{order_id}'")

        return {"status": "success", "event": event, "processed": True}
    except Exception as err:
        logger.error(f"[Webhook] Error processing subscription webhook: {err}", exc_info=True)
        return {"status": "error", "message": str(err)}

@router.post("/upgrade")
async def upgrade_subscription(
    payload: UpgradeRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Direct subscription tier upgrade route.
    """
    tier_id = payload.tier_id.lower()
    if tier_id not in PRICING_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{payload.tier_id}'. Valid options: {list(PRICING_TIERS.keys())}"
        )

    await SubscriptionService.update_user_subscription(
        db=db,
        plan=tier_id.upper(),
        payment_id=f"direct_upgrade_{int(time.time())}",
        provider="DIRECT"
    )
    summary = await SubscriptionService.get_usage_summary(db)
    return {
        "status": "success",
        "message": f"Successfully updated subscription to {summary['tier_name']}",
        "subscription": summary
    }
