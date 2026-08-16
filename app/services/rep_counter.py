class RepCounterService:

    def process_frame(self, data):
        movement = data["movement"]
        frame = data["frame_data"]

        # Placeholder logic — replace with your edge AI model
        angle = frame.get("angle", 0)
        velocity = frame.get("velocity", 0)

        rep_detected = angle > 140 and velocity > 0.5

        return {
            "movement": movement,
            "rep_detected": rep_detected,
            "angle": angle,
            "velocity": velocity
        }
