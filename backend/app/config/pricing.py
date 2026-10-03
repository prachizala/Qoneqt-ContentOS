from typing import Dict, Any, Optional

PRICING_TIERS: Dict[str, Dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_inr": 0,
        "price_display": "₹0",
        "billing_period": "/month",
        "badge": "Starter",
        "description": "Essential AI tools to get started with automated video creation.",
        "video_limit_monthly": 2,
        "script_limit_monthly": 10,
        "features": {
            "ai_videos": "2/month",
            "ai_scripts": "10/month",
            "ai_visuals": "Limited",
            "ai_voice": "Basic",
            "brand_kit": "1",
            "ai_quality_check": True,
            "qoneqt_publishing": True,
            "analytics": "Basic",
            "team_members": "1",
            "autopilot": False,
            "priority_processing": "No"
        },
        "button_text": "Current Plan",
        "is_popular": False
    },
    "creator": {
        "id": "creator",
        "name": "Creator",
        "price_inr": 499,
        "price_display": "₹499",
        "billing_period": "/month",
        "badge": "Popular",
        "description": "High-volume generation and premium assets for active creators.",
        "video_limit_monthly": 15,
        "script_limit_monthly": 100,
        "features": {
            "ai_videos": "15/month",
            "ai_scripts": "100/month",
            "ai_visuals": "Yes",
            "ai_voice": "Premium",
            "brand_kit": "3",
            "ai_quality_check": True,
            "qoneqt_publishing": True,
            "analytics": "Advanced",
            "team_members": "2",
            "autopilot": True,
            "priority_processing": "Yes (✓)"
        },
        "button_text": "Upgrade to Creator",
        "is_popular": True
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_inr": 1499,
        "price_display": "₹1,499",
        "billing_period": "/month",
        "badge": "Best Value",
        "description": "Maximum AI generation capacity with deep AI insights & priority queues.",
        "video_limit_monthly": 50,
        "script_limit_monthly": 999999, # Unlimited
        "features": {
            "ai_videos": "50/month",
            "ai_scripts": "Unlimited",
            "ai_visuals": "Yes",
            "ai_voice": "Premium",
            "brand_kit": "10",
            "ai_quality_check": "Advanced",
            "qoneqt_publishing": True,
            "analytics": "Advanced + AI Insights",
            "team_members": "5",
            "autopilot": True,
            "priority_processing": "High (✓✓)"
        },
        "button_text": "Upgrade to Pro",
        "is_popular": False
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_inr": -1,
        "price_display": "Custom",
        "billing_period": "",
        "badge": "Custom",
        "description": "Bespoke AI pipelines, custom cloned voices, dedicated GPU cluster.",
        "video_limit_monthly": 999999, # Unlimited
        "script_limit_monthly": 999999, # Unlimited
        "features": {
            "ai_videos": "Unlimited*",
            "ai_scripts": "Unlimited",
            "ai_visuals": "Yes",
            "ai_voice": "Custom Voice",
            "brand_kit": "Unlimited",
            "ai_quality_check": True,
            "qoneqt_publishing": True,
            "analytics": "Full Analytics",
            "team_members": "Custom",
            "autopilot": True,
            "priority_processing": "Highest (✓✓✓)"
        },
        "button_text": "Contact Sales",
        "is_popular": False
    }
}

def get_tier_config(tier_id: str) -> Dict[str, Any]:
    return PRICING_TIERS.get(tier_id.lower(), PRICING_TIERS["free"])
