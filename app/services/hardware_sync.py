from datetime import datetime

from sqlalchemy.orm import Session

from app.models.hardware import UserDevice


class HardwareSyncService:
    def _get_device(self, db: Session, user_id: int, provider: str):
        return (
            db.query(UserDevice)
            .filter(UserDevice.user_id == user_id, UserDevice.provider == provider)
            .first()
        )

    def link_device(self, db: Session, data: dict):
        user_id = data["user_id"]
        provider = data["provider"].lower()
        device = self._get_device(db, user_id, provider)

        if device:
            device.access_token = data["access_token"]
            device.refresh_token = data.get("refresh_token")
            device.linked_at = datetime.utcnow()
            device.status = "linked"
        else:
            device = UserDevice(
                user_id=user_id,
                provider=provider,
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                status="linked",
            )
            db.add(device)

        db.commit()
        db.refresh(device)
        return {"message": "Device linked successfully.", "provider": provider}

    def unlink_device(self, db: Session, user_id: int, provider: str):
        device = self._get_device(db, user_id, provider.lower())
        if not device:
            return {"message": "Device was not linked.", "provider": provider.lower()}
        db.delete(device)
        db.commit()
        return {"message": "Device unlinked successfully.", "provider": provider.lower()}

    def sync_device(self, db: Session, user_id: int, provider: str):
        device = self._get_device(db, user_id, provider.lower())
        if not device:
            raise ValueError("Device is not linked.")

        # Placeholder values until provider-specific API clients are wired in.
        synced_data = {
            "steps": 12000,
            "heart_rate": 62,
            "sleep_hours": 7.8,
            "calories": 2300,
            "distance_km": 8.4,
            "synced_at": datetime.utcnow(),
        }
        device.last_sync = synced_data["synced_at"]
        device.status = "synced"
        db.commit()
        return synced_data

    def get_last_sync(self, db: Session, user_id: int, provider: str):
        device = self._get_device(db, user_id, provider.lower())
        return {"last_sync": device.last_sync if device else None}

    def get_device_status(self, db: Session, user_id: int, provider: str):
        device = self._get_device(db, user_id, provider.lower())
        return {"status": device.status if device else None}
