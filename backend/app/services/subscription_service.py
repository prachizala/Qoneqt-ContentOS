import os
import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.models import Project, UserSubscription, SubscriptionPlan
from backend.app.config.pricing import PRICING_TIERS, get_tier_config

logger = logging.getLogger(__name__)

# In-memory mock subscription tier store override fallback
_CURRENT_TIER_OVERRIDE: Optional[str] = None

class SubscriptionService:
    """
    Service managing persistent UserSubscription database state, Razorpay/Stripe billing cycles,
    quota enforcement, and Creator plan upgrades.
    """
    @classmethod
    def get_current_tier_id(cls) -> str:
        if _CURRENT_TIER_OVERRIDE:
            return _CURRENT_TIER_OVERRIDE.lower()
        return os.getenv("SUBSCRIPTION_TIER", "free").lower()

    @classmethod
    def set_current_tier_id(cls, tier_id: str) -> str:
        global _CURRENT_TIER_OVERRIDE
        if tier_id.lower() in PRICING_TIERS:
            _CURRENT_TIER_OVERRIDE = tier_id.lower()
            logger.info(f"[SubscriptionService] Active tier updated to '{_CURRENT_TIER_OVERRIDE}'")
            return _CURRENT_TIER_OVERRIDE
        return cls.get_current_tier_id()

    @classmethod
    async def get_or_create_user_subscription(
        cls, db: AsyncSession, user_id: str = "default_user"
    ) -> UserSubscription:
        """
        Retrieves or initializes persistent user subscription record in database.
        """
        stmt = select(UserSubscription).where(UserSubscription.user_id == user_id)
        result = await db.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            now = datetime.datetime.now(datetime.timezone.utc)
            reset_date = now + datetime.timedelta(days=30)
            
            # Sync with env override if set
            override_tier = cls.get_current_tier_id().upper()
            plan_str = override_tier if override_tier in ("FREE", "CREATOR", "PRO", "ENTERPRISE") else "FREE"
            v_limit = 15 if plan_str == "CREATOR" else (50 if plan_str == "PRO" else 2)
            s_limit = 100 if plan_str == "CREATOR" else (999 if plan_str == "PRO" else 10)

            sub = UserSubscription(
                user_id=user_id,
                plan=plan_str,
                subscription_status="ACTIVE",
                videos_limit=v_limit,
                scripts_limit=s_limit,
                reset_date=reset_date,
                payment_provider="RAZORPAY"
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            logger.info(f"[SubscriptionService] Initialized default UserSubscription for '{user_id}' with plan '{plan_str}'")

        # Sync in-memory override if DB record differs
        if _CURRENT_TIER_OVERRIDE and _CURRENT_TIER_OVERRIDE.upper() != sub.plan:
            sub.plan = _CURRENT_TIER_OVERRIDE.upper()
            if sub.plan == "CREATOR":
                sub.videos_limit = 15
                sub.scripts_limit = 100
            elif sub.plan == "PRO":
                sub.videos_limit = 50
                sub.scripts_limit = 999999
            await db.commit()

        return sub

    @classmethod
    async def update_user_subscription(
        cls,
        db: AsyncSession,
        plan: str,
        payment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        provider: str = "RAZORPAY",
        user_id: str = "default_user"
    ) -> UserSubscription:
        """
        Updates persistent database subscription status upon payment capture/webhook success.
        Sets: plan='CREATOR', subscription_status='ACTIVE', videos_limit=15, scripts_limit=100, reset_date=now()+30d.
        """
        sub = await cls.get_or_create_user_subscription(db, user_id=user_id)
        plan_upper = plan.upper()

        sub.plan = plan_upper
        sub.subscription_status = "ACTIVE"
        sub.payment_provider = provider
        if payment_id:
            sub.payment_id = payment_id
        if order_id:
            sub.order_id = order_id

        now = datetime.datetime.now(datetime.timezone.utc)
        sub.reset_date = now + datetime.timedelta(days=30)

        if plan_upper == "CREATOR":
            sub.videos_limit = 15
            sub.scripts_limit = 100
        elif plan_upper == "PRO":
            sub.videos_limit = 50
            sub.scripts_limit = 999999
        elif plan_upper == "ENTERPRISE":
            sub.videos_limit = 999999
            sub.scripts_limit = 999999
        else:
            sub.videos_limit = 2
            sub.scripts_limit = 10

        cls.set_current_tier_id(plan.lower())

        await db.commit()
        await db.refresh(sub)
        logger.info(
            f"[SubscriptionService] Upgraded UserSubscription for '{user_id}' to '{sub.plan}' "
            f"(videos_limit={sub.videos_limit}, reset_date={sub.reset_date})"
        )
        return sub

    @classmethod
    async def get_monthly_video_usage(
        cls, db: AsyncSession, start_time: Optional[datetime.datetime] = None
    ) -> int:
        """
        Calculates the number of video projects created during current billing cycle.
        """
        if not start_time:
            now = datetime.datetime.now(datetime.timezone.utc)
            start_time = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)

        stmt = select(func.count(Project.id)).where(Project.created_at >= start_time)
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return int(count)

    @classmethod
    async def get_usage_summary(
        cls, db: AsyncSession, user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Returns full subscription, quota, reset date, and usage summary.
        """
        sub = await cls.get_or_create_user_subscription(db, user_id=user_id)
        tier_id = sub.plan.lower()
        tier = get_tier_config(tier_id)

        # Calculate usage within current billing cycle
        start_billing_period = (
            sub.reset_date - datetime.timedelta(days=30)
            if sub.reset_date
            else datetime.datetime.now(datetime.timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        )
        monthly_videos_used = await cls.get_monthly_video_usage(db, start_time=start_billing_period)

        limit = sub.videos_limit
        remaining = max(0, limit - monthly_videos_used) if limit < 999999 else "Unlimited"

        return {
            "tier_id": tier_id,
            "tier_name": tier["name"],
            "plan": sub.plan,
            "subscription_status": sub.subscription_status,
            "price_display": tier["price_display"],
            "billing_period": tier["billing_period"],
            "monthly_videos_limit": limit if limit < 999999 else "Unlimited",
            "monthly_scripts_limit": sub.scripts_limit,
            "monthly_videos_used": monthly_videos_used,
            "monthly_videos_remaining": remaining,
            "reset_date": sub.reset_date.isoformat() if sub.reset_date else None,
            "limit_reached": monthly_videos_used >= limit if limit < 999999 else False,
            "payment_id": sub.payment_id,
            "order_id": sub.order_id,
            "tier_details": tier
        }

    @classmethod
    async def enforce_video_generation_limit(
        cls, db: AsyncSession, user_id: str = "default_user"
    ) -> None:
        """
        Enforces monthly tier limits before video project pipeline execution.
        Raises HTTP 403 Forbidden with detailed upgrade payload if limit is reached.
        """
        summary = await cls.get_usage_summary(db, user_id=user_id)
        limit = summary["monthly_videos_limit"]

        if limit == "Unlimited" or (isinstance(limit, int) and limit >= 999999):
            return

        used = summary["monthly_videos_used"]
        tier_name = summary["tier_name"]

        if isinstance(limit, int) and used >= limit:
            msg = (
                f"Monthly video generation limit reached ({used}/{limit} for {tier_name} tier). "
                f"Upgrade to Creator (₹499/mo) or Pro (₹1,499/mo) to continue generating."
            )
            logger.warning(f"[SubscriptionGate] {msg}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "TIER_LIMIT_REACHED",
                    "message": msg,
                    "current_tier": tier_name,
                    "plan": summary["plan"],
                    "used": used,
                    "limit": limit,
                    "reset_date": summary["reset_date"],
                    "upgrade_url": "/pricing"
                }
            )
