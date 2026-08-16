from datetime import datetime


class LiveSyncService:

    # ---------------------------------------------------------
    # Join Live Class
    # ---------------------------------------------------------
    def join_class(self, db, data):
        record = {
            "user_id": data["user_id"],
            "class_id": data["class_id"],
            "joined_at": datetime.utcnow()
        }

        db.execute("""
            INSERT INTO live_class_attendance (user_id, class_id, joined_at)
            VALUES (:user_id, :class_id, :joined_at)
        """, record)

        db.commit()
        return {"status": "joined", "class_id": data["class_id"]}

    # ---------------------------------------------------------
    # Start Live Coaching
    # ---------------------------------------------------------
    def start_coaching(self, db, data):
        record = {
            "user_id": data["user_id"],
            "coach_id": data["coach_id"],
            "started_at": datetime.utcnow()
        }

        db.execute("""
            INSERT INTO live_coaching_sessions (user_id, coach_id, started_at)
            VALUES (:user_id, :coach_id, :started_at)
        """, record)

        db.commit()
        return {"status": "coaching_started"}

    # ---------------------------------------------------------
    # Offline Sync
    # ---------------------------------------------------------
    def sync_offline(self, db, data):
        record = {
            "user_id": data["user_id"],
            "payload": str(data["payload"]),
            "synced_at": datetime.utcnow()
        }

        db.execute("""
            INSERT INTO offline_sync (user_id, payload, synced_at)
            VALUES (:user_id, :payload, :synced_at)
        """, record)

        db.commit()
        return {"status": "synced"}
