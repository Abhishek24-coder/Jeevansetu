from datetime import datetime, timedelta, timezone

from app.ai_pipeline.models.pipeline import UserVerificationRequest


class VerificationService:
    TIMEOUT_SECONDS = 15

    @classmethod
    def create_request(cls, incident_id: str) -> UserVerificationRequest:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=cls.TIMEOUT_SECONDS)
        return UserVerificationRequest(
            incident_id=incident_id,
            message="Possible accident detected. Confirm you are safe within 15 seconds to cancel escalation.",
            expires_at=expires_at,
            timeout_seconds=cls.TIMEOUT_SECONDS,
        )
