from datetime import datetime
from typing import Any, Dict

from supabase import Client

from database.supabase_client import supabase
from utils.logger import get_logger

logger = get_logger("subscription_service")


class SubscriptionService:
    def __init__(self, db: Client = supabase):
        self.db = db

    def has_active_subscription(
        self, user_id: str, subscription_type: str = "core_interview"
    ) -> bool:
        # Check if a user has an active subscription of the given type
        if not user_id:
            logger.error("No user_id found.")
            return False

        try:
            response = (
                self.db.table("user_subscription")
                .select("*")
                .eq("user_id", user_id)
                .eq("subscription_type", subscription_type)
                .eq("status", "active")
                .maybe_single()
                .execute()
            )

            if response is None or response.data is None or not response.data:
                logger.info(
                    f"No active {subscription_type} subscription found for user {user_id}"
                )
                return False

            # Check if subscription has expired
            if not isinstance(response.data, dict):
                logger.error(f"Expected dict, got {type(response.data).__name__}")
                return False
            subscription: Dict[str, Any] = response.data

            # Check end_date if present
            end_date = subscription.get("end_date")
            if end_date:
                # Ensure it's a string before passing to fromisoformat
                end_date_str = str(end_date)
                end_date_dt = datetime.fromisoformat(end_date_str)
                if datetime.now() > end_date_dt:
                    # Auto-expire the subscription
                    subscription_id = subscription.get("id")
                    if subscription_id:
                        self.expire_subscription(str(subscription_id))
                    return False

            logger.info(f"User {user_id} has active {subscription_type} subscription")
            return True

        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id}: {e}")
            return False

    def expire_subscription(self, subscription_id: str) -> bool:
        # Mark a subscription as expired
        try:
            self.db.table("user_subscriptions").update({"status": "expired"}).eq(
                "id", subscription_id
            ).execute()
            logger.info(f"Subscription {subscription_id} marked as expired")
            return True
        except Exception as e:
            logger.error(f"Error expiring subscription {subscription_id}: {e}")
            return False
