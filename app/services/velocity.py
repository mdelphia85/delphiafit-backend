from typing import Dict, Any, List
import math


class VelocityEngine:
    """
    Full velocity-based training engine.

    Responsibilities:
    - Estimate bar speed per rep
    - Compute velocity curves
    - Calculate peak & average velocity
    - Estimate power output
    - Compute velocity loss (fatigue indicator)
    - Provide auto-regulation signals
    """

    # ---------------------------------------------------------
    # Public: Estimate Velocity Package
    # ---------------------------------------------------------
    def estimate(self, rep_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        rep_data structure expected:
        {
            "positions": [
                {"frame": 0, "y": 120},
                {"frame": 1, "y": 118},
                {"frame": 2, "y": 115},
                ...
            ],
            "timestamps": [0.00, 0.033, 0.066, ...],
            "load": 225,  # lbs or kg (frontend decides)
            "exercise": "squat" | "bench" | "deadlift" | ...
        }
        """

        positions = rep_data.get("positions", [])
        timestamps = rep_data.get("timestamps", [])
        load = rep_data.get("load", 0)
        exercise = rep_data.get("exercise", "unknown")

        if len(positions) < 2 or len(timestamps) < 2:
            return {
                "error": "Insufficient data for velocity estimation."
            }

        velocities = self._compute_velocities(positions, timestamps)
        peak_velocity = max(velocities)
        avg_velocity = sum(velocities) / len(velocities)

        power_output = self._power_output(load, avg_velocity)
        velocity_loss = self._velocity_loss(velocities)
        fatigue = self._fatigue_score(velocity_loss)

        return {
            "exercise": exercise,
            "peak_velocity": round(peak_velocity, 3),
            "avg_velocity": round(avg_velocity, 3),
            "velocity_curve": [round(v, 3) for v in velocities],
            "power_output": round(power_output, 2),
            "velocity_loss": round(velocity_loss, 3),
            "fatigue_score": fatigue,
            "auto_regulation": self._auto_regulation_signal(fatigue, avg_velocity),
        }

    # ---------------------------------------------------------
    # Compute Velocities
    # ---------------------------------------------------------
    def _compute_velocities(self, positions: List[Dict[str, Any]], timestamps: List[float]) -> List[float]:
        velocities = []

        for i in range(1, len(positions)):
            dy = positions[i]["y"] - positions[i - 1]["y"]
            dt = timestamps[i] - timestamps[i - 1]

            if dt <= 0:
                velocities.append(0.0)
            else:
                velocities.append(abs(dy / dt))

        return velocities

    # ---------------------------------------------------------
    # Power Output
    # ---------------------------------------------------------
    def _power_output(self, load: float, avg_velocity: float) -> float:
        """
        Simple power estimation:
        Power = Force * Velocity
        Force approximated as load * 9.81 (gravity)
        """

        force = load * 9.81
        return force * avg_velocity

    # ---------------------------------------------------------
    # Velocity Loss (Fatigue Indicator)
    # ---------------------------------------------------------
    def _velocity_loss(self, velocities: List[float]) -> float:
        if not velocities:
            return 0.0

        peak = max(velocities)
        last = velocities[-1]

        if peak == 0:
            return 0.0

        return (peak - last) / peak

    # ---------------------------------------------------------
    # Fatigue Score (0–100)
    # ---------------------------------------------------------
    def _fatigue_score(self, velocity_loss: float) -> int:
        """
        Velocity loss thresholds:
        < 0.10 → low fatigue
        0.10–0.30 → moderate fatigue
        > 0.30 → high fatigue
        """

        if velocity_loss < 0.10:
            return 20
        if velocity_loss < 0.30:
            return 50
        return 80

    # ---------------------------------------------------------
    # Auto-Regulation Signal
    # ---------------------------------------------------------
    def _auto_regulation_signal(self, fatigue: int, avg_velocity: float) -> str:
        if fatigue >= 80:
            return "stop set — high fatigue detected"
        if fatigue >= 50:
            return "reduce load by 5–10%"
        if avg_velocity < 0.3:
            return "reduce load — velocity too slow"
        return "continue — velocity and fatigue acceptable"
