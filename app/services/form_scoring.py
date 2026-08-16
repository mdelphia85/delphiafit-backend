from typing import Dict, Any, List
import math


class FormScoringEngine:
    """
    Full biomechanics + form scoring engine.

    Responsibilities:
    - Joint angle estimation
    - Rep segmentation
    - Stability scoring
    - Tempo analysis
    - Depth / ROM scoring
    - Symmetry scoring
    - Technique recommendations
    """

    # ---------------------------------------------------------
    # Public: Score Form
    # ---------------------------------------------------------
    def score(self, motion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        motion_data structure expected:
        {
            "keypoints": [
                {"frame": 0, "points": {"shoulder": (x,y), "elbow": (x,y), ...}},
                {"frame": 1, "points": {...}},
                ...
            ],
            "reps": [
                {"start_frame": 10, "end_frame": 40},
                {"start_frame": 45, "end_frame": 75},
            ],
            "exercise": "squat" | "bench" | "deadlift" | ...
        }
        """

        keypoints = motion_data.get("keypoints", [])
        reps = motion_data.get("reps", [])
        exercise = motion_data.get("exercise", "unknown")

        rep_scores = []
        for rep in reps:
            rep_scores.append(self._score_rep(rep, keypoints, exercise))

        final_score = sum(r["score"] for r in rep_scores) / max(1, len(rep_scores))

        return {
            "exercise": exercise,
            "final_score": round(final_score, 2),
            "rep_breakdown": rep_scores,
            "recommendations": self._overall_recommendations(final_score, exercise),
        }

    # ---------------------------------------------------------
    # Score a Single Rep
    # ---------------------------------------------------------
    def _score_rep(self, rep: Dict[str, int], keypoints: List[Dict[str, Any]], exercise: str) -> Dict[str, Any]:
        start = rep["start_frame"]
        end = rep["end_frame"]

        rep_frames = keypoints[start:end+1]

        angles = self._compute_joint_angles(rep_frames)
        stability = self._stability_score(rep_frames)
        tempo = self._tempo_score(rep_frames)
        depth = self._depth_score(rep_frames, exercise)
        symmetry = self._symmetry_score(rep_frames)

        score = (
            angles["score"] * 0.25 +
            stability * 0.25 +
            tempo * 0.20 +
            depth * 0.20 +
            symmetry * 0.10
        )

        return {
            "rep_range": (start, end),
            "score": round(score, 2),
            "angles": angles,
            "stability": stability,
            "tempo": tempo,
            "depth": depth,
            "symmetry": symmetry,
            "rep_recommendations": self._rep_recommendations(score, angles, stability, tempo, depth, symmetry),
        }

    # ---------------------------------------------------------
    # Joint Angle Estimation
    # ---------------------------------------------------------
    def _compute_joint_angles(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes average angles for major joints:
        - knee
        - hip
        - elbow
        - shoulder
        """

        def angle(p1, p2, p3):
            # Compute angle at p2 formed by p1 -> p2 -> p3
            try:
                a = math.dist(p2, p1)
                b = math.dist(p2, p3)
                c = math.dist(p1, p3)
                return math.degrees(math.acos((a*a + b*b - c*c) / (2*a*b)))
            except:
                return 0

        knee_angles = []
        hip_angles = []
        elbow_angles = []
        shoulder_angles = []

        for f in frames:
            pts = f["points"]

            if {"hip", "knee", "ankle"} <= pts.keys():
                knee_angles.append(angle(pts["hip"], pts["knee"], pts["ankle"]))

            if {"shoulder", "hip", "knee"} <= pts.keys():
                hip_angles.append(angle(pts["shoulder"], pts["hip"], pts["knee"]))

            if {"shoulder", "elbow", "wrist"} <= pts.keys():
                elbow_angles.append(angle(pts["shoulder"], pts["elbow"], pts["wrist"]))

            if {"elbow", "shoulder", "hip"} <= pts.keys():
                shoulder_angles.append(angle(pts["elbow"], pts["shoulder"], pts["hip"]))

        avg_knee = sum(knee_angles) / max(1, len(knee_angles))
        avg_hip = sum(hip_angles) / max(1, len(hip_angles))
        avg_elbow = sum(elbow_angles) / max(1, len(elbow_angles))
        avg_shoulder = sum(shoulder_angles) / max(1, len(shoulder_angles))

        # Angle scoring: closer to expected ranges = better
        score = self._angle_score(avg_knee, avg_hip, avg_elbow, avg_shoulder)

        return {
            "knee": round(avg_knee, 2),
            "hip": round(avg_hip, 2),
            "elbow": round(avg_elbow, 2),
            "shoulder": round(avg_shoulder, 2),
            "score": score,
        }

    def _angle_score(self, knee, hip, elbow, shoulder) -> float:
        """
        Scores angles based on typical biomechanical ranges.
        """

        def range_score(angle, low, high):
            if angle < low or angle > high:
                return 0.5
            return 1.0

        knee_s = range_score(knee, 70, 140)
        hip_s = range_score(hip, 60, 130)
        elbow_s = range_score(elbow, 45, 160)
        shoulder_s = range_score(shoulder, 30, 120)

        return round((knee_s + hip_s + elbow_s + shoulder_s) / 4, 2)

    # ---------------------------------------------------------
    # Stability Score
    # ---------------------------------------------------------
    def _stability_score(self, frames: List[Dict[str, Any]]) -> float:
        """
        Measures movement smoothness by tracking center-of-mass jitter.
        """

        com_positions = []
        for f in frames:
            pts = f["points"]
            if {"hip", "shoulder"} <= pts.keys():
                x = (pts["hip"][0] + pts["shoulder"][0]) / 2
                y = (pts["hip"][1] + pts["shoulder"][1]) / 2
                com_positions.append((x, y))

        if len(com_positions) < 2:
            return 0.5

        jitter = 0
        for i in range(1, len(com_positions)):
            jitter += math.dist(com_positions[i], com_positions[i - 1])

        avg_jitter = jitter / len(com_positions)

        if avg_jitter < 5:
            return 1.0
        if avg_jitter < 10:
            return 0.8
        if avg_jitter < 20:
            return 0.6
        return 0.4

    # ---------------------------------------------------------
    # Tempo Score
    # ---------------------------------------------------------
    def _tempo_score(self, frames: List[Dict[str, Any]]) -> float:
        """
        Evaluates rep tempo consistency.
        """

        frame_count = len(frames)

        if frame_count < 10:
            return 0.6

        if frame_count < 20:
            return 0.8

        return 1.0

    # ---------------------------------------------------------
    # Depth / ROM Score
    # ---------------------------------------------------------
    def _depth_score(self, frames: List[Dict[str, Any]], exercise: str) -> float:
        """
        Scores depth based on exercise type.
        """

        if exercise == "squat":
            # Look at hip vs knee height
            depths = []
            for f in frames:
                pts = f["points"]
                if {"hip", "knee"} <= pts.keys():
                    depths.append(pts["hip"][1] - pts["knee"][1])

            if not depths:
                return 0.5

            avg_depth = sum(depths) / len(depths)

            if avg_depth < -10:
                return 1.0
            if avg_depth < 0:
                return 0.8
            return 0.5

        # Default ROM scoring
        return 0.8

    # ---------------------------------------------------------
    # Symmetry Score
    # ---------------------------------------------------------
    def _symmetry_score(self, frames: List[Dict[str, Any]]) -> float:
        """
        Compares left vs right side movement.
        """

        diffs = []
        for f in frames:
            pts = f["points"]
            if {"left_shoulder", "right_shoulder"} <= pts.keys():
                diffs.append(abs(pts["left_shoulder"][1] - pts["right_shoulder"][1]))

        if not diffs:
            return 0.8

        avg_diff = sum(diffs) / len(diffs)

        if avg_diff < 5:
            return 1.0
        if avg_diff < 10:
            return 0.8
        return 0.6

    # ---------------------------------------------------------
    # Rep Recommendations
    # ---------------------------------------------------------
    def _rep_recommendations(self, score, angles, stability, tempo, depth, symmetry) -> List[str]:
        recs = []

        if score < 0.7:
            recs.append("Focus on smoother tempo and consistent movement.")
        if angles["score"] < 0.8:
            recs.append("Improve joint positioning for better biomechanics.")
        if stability < 0.8:
            recs.append("Reduce wobble by bracing your core.")
        if depth < 0.8:
            recs.append("Increase range of motion safely.")
        if symmetry < 0.8:
            recs.append("Work on left/right balance and control.")

        return recs

    # ---------------------------------------------------------
    # Overall Recommendations
    # ---------------------------------------------------------
    def _overall_recommendations(self, final_score: float, exercise: str) -> List[str]:
        if final_score >= 0.9:
            return ["Excellent form — keep doing what you're doing."]
        if final_score >= 0.75:
            return ["Solid form — refine tempo and stability for even better performance."]
        if final_score >= 0.6:
            return ["Form needs improvement — focus on control, depth, and consistency."]
        return ["Significant form issues — reduce load and prioritize technique."]
