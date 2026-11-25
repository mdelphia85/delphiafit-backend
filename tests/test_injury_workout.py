"""Behavioral regression tests for no-cost, question-specific workout modifications."""
import pytest

from app.services.ai_engine import AIEngine


def _answer(prompt: str, **user_data) -> str:
    return AIEngine().coach(user_data, prompt)["coach_response"]


def test_original_right_knee_request_returns_modified_workout_not_only_a_warning():
    answer = _answer(
        "right knee pain, i need a workout that wont cause more damage",
        fatigue=3,
        sleep_hours=7,
    )
    assert "right knee pain" in answer
    assert "Modified upper-body workout option" in answer
    assert "Warm-up" in answer
    assert "Main work" in answer
    assert "Cool-down" in answer
    assert "Seated light biceps curls" in answer
    assert "Skip squats, lunges" in answer
    assert "not clearance to train" in answer
    assert "no workout can be guaranteed" in answer


def test_dumbbells_and_time_change_the_knee_workout():
    answer = _answer(
        "right knee pain, create a 10-minute dumbbell workout to build muscle",
        fatigue=3,
    )
    assert "Modified upper-body strength option (about 10 minutes" in answer
    assert "1 set of 6-10" in answer
    assert "Seated light dumbbell curls" in answer
    assert "Seated light dumbbell lateral raises" in answer
    assert "squat" in answer.lower()
    assert "seated band rows" not in answer


def test_bands_generate_band_workout_without_knee_anchor():
    answer = _answer("left knee hurts; I need a 25-minute resistance band workout")
    assert "left knee pain" in answer
    assert "about 25 minutes" in answer
    assert "2 sets of 8-12" in answer
    assert "Seated resistance-band rows" in answer
    assert "Do not improvise an anchor" in answer
    assert "painful knee" in answer


def test_knee_cardio_request_does_not_offer_strength_or_running():
    answer = _answer("Knee pain. Modify my 20 minute cardio workout.")
    assert "Knee-sparing cardio alternative" in answer
    assert "up to 20 minutes" in answer
    assert "upper-body ergometer" in answer
    assert "Avoid running, jumping" in answer
    assert "biceps curls" not in answer


def test_no_equipment_knee_workout_is_not_misrepresented_as_strength_training():
    answer = _answer("My knee hurts, I need a home workout with no equipment")
    assert "Seated shoulder-blade squeezes" in answer
    assert "not a full strength substitute" in answer
    assert "Seated light biceps curls" not in answer


def test_severe_fatigue_is_prioritized_over_knee_training():
    answer = _answer("My knee hurts, modify my workout", fatigue=9)
    assert "consider rest today" in answer
    assert "Main work" not in answer


@pytest.mark.parametrize("prompt", [
    "My knee hurts badly and I can't bear weight. Need a workout.",
    "I have chest pain and knee pain. What workout should I do?",
    "I have severe knee pain. Modify my workout.",
])
def test_urgent_symptoms_do_not_return_a_workout(prompt):
    answer = _answer(prompt)
    assert "Do not exercise" in answer
    assert "Modified upper-body" not in answer


def test_unrelated_knee_question_does_not_receive_unsolicited_workout():
    answer = _answer("My knee hurts. What might be going on?")
    assert "which movements make it worse" in answer
    assert "Main work" not in answer


def test_other_areas_are_not_mistaken_for_knee_pain():
    answer = _answer("My shoulder hurts, give me a workout")
    assert "affected area" in answer
    assert "Modified upper-body workout option" not in answer


def test_knee_in_saved_injury_profile_is_used_to_modify_workout():
    answer = _answer("Give me a workout", injuries=["right knee injury"])
    assert "Modified upper-body workout option" in answer
    assert "Skip squats, lunges" in answer
