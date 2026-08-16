from datetime import datetime
from sqlalchemy.orm import Session


class HardwareSyncService:

    # ---------------------------------------------------------
    # Link Device
    # ---------------------------------------------------------
    def link_device(self, db: Session, data: dict):
        user_id = data["user_id"]
        provider = data["provider"]

        record = {
            "user_id": user_id,
            "provider": provider,
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "linked_at": datetime.utcnow(),
            "last_sync": None,
            "status": "linked"
        }

        # store in your device table (you will create this later)
        db.execute("""
            INSERT INTO user_devices (user_id, provider, access_token, refresh_token, linked_at, status)
            VALUES (:user_id, :provider, :access_token, :refresh_token, :linked_at, :status)
        """, record)

        db.commit()
        return {"message": "Device linked successfully.", "provider": provider}

    # ---------------------------------------------------------
    # Unlink Device
    # ---------------------------------------------------------
    def unlink_device(self, db: Session, user_id: int, provider: str):
        db.execute("""
            DELETE FROM user_devices
            WHERE user_id = :user_id AND provider = :provider
        """, {"user_id": user_id, "provider": provider})

        db.commit()
        return {"message": "Device unlinked successfully."}

    # ---------------------------------------------------------
    # Sync Device
    # ---------------------------------------------------------
    def sync_device(self, db: Session, user_id: int, provider: str):
        # placeholder for actual API calls
        synced_data = {
            "steps": 12000,
            "heart_rate": 62,
            "sleep_hours": 7.8,
            "calories": 2300,
            "distance_km": 8.4,
            "synced_at": datetime.utcnow()
        }

        db.execute("""
            UPDATE user_devices
            SET last_sync = :synced_at, status = 'synced'
            WHERE user_id = :user_id AND provider = :provider
        """, {
            "user_id": user_id,
            "provider": provider,
            "synced_at": synced_data["synced_at"]
        })

        db.commit()
        return synced_data

    # ---------------------------------------------------------
    # Get Last Sync
    # ---------------------------------------------------------
    def get_last_sync(self, db: Session, user_id: int, provider: str):
        result = db.execute("""
            SELECT last_sync FROM user_devices
            WHERE user_id = :user_id AND provider = :provider
        """, {"user_id": user_id, "provider": provider}).fetchone()

        return {"last_sync": result[0] if result else None}

    # ---------------------------------------------------------
    # Get Device Status
    # ---------------------------------------------------------
    def get_device_status(self, db: Session, user_id: int, provider: str):
        result = db.execute("""
            SELECT status FROM user_devices
            WHERE user_id = :user_id AND provider = :provider
        """, {"user_id": user_id, "provider": provider}).fetchone()

        return {"status": result[0] if result else None}
