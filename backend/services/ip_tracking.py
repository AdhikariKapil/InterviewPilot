from datetime import datetime, timedelta

from supabase import Client

from database.supabase_client import supabase
from utils.logger import get_logger

logger = get_logger("ip_tracking")


class IPTrackingService:
    def __init__(self, db: Client = supabase):
        self.db = db

    def get_ip_usage(self, ip: str) -> dict | None:
        try:
            response = (
                self.db.table("ip_usage")
                .select("*")
                .eq("ip_address", ip)
                .maybe_single()
                .execute()
            )

            if response is None or response.data is None:
                logger.info("response.data from ip_usage query is None")
                return None

            if not isinstance(response.data, dict):
                logger.error(
                    f"Excepted dict from ip_usage query got: {type(response.data).__name__}"
                )
                raise TypeError(
                    f"Excepted dict from ip_usage query, got{type(response.data).__name__}"
                )

            return response.data
        except Exception as error:
            logger.error(f"Error fetching IP usage for {ip}: {error}")
            return None

    def create_ip_record(self, ip: str) -> dict | None:
        # Create a new IP record with interview_count = 0
        try:
            response = (
                self.db.table("ip_usage")
                .insert(
                    {
                        "ip_address": ip,
                        "interview_count": 0,
                        "last_reset": datetime.now().isoformat(),
                    }
                )
                .execute()
            )
            if response is None or response.data is None:
                logger.info("response.data while creating IP record is None")
                return None
            if not isinstance(response.data, dict):
                logger.error(
                    f"Excepted dict from ip_usage creating record: {type(response.data).__name__}"
                )
                raise TypeError(
                    f"Excepted dict from ip_usage creating record: {type(response.data).__name__}"
                )
        except Exception as error:
            logger.error(f"Error creating IP record for {ip}: {error}")
            return None

    def reset_ip_count(self, ip: str) -> bool:
        """Reset interview count to 0 and update last_reset."""
        try:
            self.db.table("ip_usage").update(
                {"interview_count": 0, "last_reset": datetime.now().isoformat()}
            ).eq("ip_address", ip).execute()
            logger.info(f"Reset count for {ip}")
            return True
        except Exception as e:
            logger.error(f"Error resetting IP count for {ip}: {e}")
            return False

    def can_access_free_tier(self, ip: str) -> bool:
        # Check if IP is within free tier limit (3 interviews).
        record = self.get_ip_usage(ip)
        if not record:
            logger.info(f"No record yet so {ip} can access")
            return True

        last_reset = datetime.fromisoformat(record["last_reset"])
        if datetime.now() - last_reset > timedelta(hours=24):
            self.reset_ip_count(ip)
            logger.info(f"Reset count after 24 hours for {ip}")
            return True

        return record["interview_count"] < 3

    def increment_ip_count(self, ip: str) -> bool:
        # Increment interview count for an IP.
        record = self.get_ip_usage(ip)
        if not record:
            self.create_ip_record(ip)
            logger.info(f"Create new record for {ip} because there is no usage.")
            return True

        try:
            new_count = record["interview_count"] + 1
            self.db.table("ip_usage").update({"interview_count": new_count}).eq(
                "ip_addrerss", ip
            ).execute()
            logger.info(f"interview_count increased by 1 for {ip}")
            return True
        except Exception as error:
            logger.error(f"Error incrementing IP count for {ip}: {error}")
            return False
