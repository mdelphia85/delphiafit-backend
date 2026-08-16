class K9Engine:

    def evaluate_detection(self, frame):
        # Placeholder logic — replace with ML model
        scent_confidence = frame.get("scent_confidence", 0.0)
        return {"detected": scent_confidence > 0.85, "confidence": scent_confidence}

    def evaluate_tracking(self, frame):
        # Placeholder logic
        track_accuracy = frame.get("track_accuracy", 0.0)
        return {"on_track": track_accuracy > 0.7, "accuracy": track_accuracy}

    def evaluate_bite_work(self, frame):
        bite_force = frame.get("bite_force", 0)
        control_score = frame.get("control_score", 0)
        return {
            "bite_force": bite_force,
            "control_score": control_score,
            "passed": bite_force > 200 and control_score > 0.8
        }
