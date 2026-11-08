from app.models.live import LiveClassAttendance, LiveCoachingSession, OfflineSyncRecord


class LiveSyncService:
    def join_class(self, db, data):
        record = LiveClassAttendance(
            user_id=data["user_id"],
            class_id=data["class_id"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "status": "joined",
            "class_id": record.class_id,
            "attendance_id": record.id,
            "joined_at": record.joined_at,
        }

    def start_coaching(self, db, data):
        record = LiveCoachingSession(
            user_id=data["user_id"],
            coach_id=data["coach_id"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "status": "coaching_started",
            "session_id": record.id,
            "started_at": record.started_at,
        }

    def sync_offline(self, db, data):
        record = OfflineSyncRecord(
            user_id=data["user_id"],
            payload=data["payload"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "status": "synced",
            "sync_id": record.id,
            "synced_at": record.synced_at,
        }
