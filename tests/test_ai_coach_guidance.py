import pytest

from app.services.ai_engine import AIEngine


@pytest.mark.parametrize("message", [
    "right knee pain, give me a work out to work around this",
    "My knee hurts; what workout can I do?",
])
def test_knee_pain_is_addressed_without_claiming_recovery(message):
    response = AIEngine().coach({"fatigue": 3, "sleep_hours": 7}, message)["coach_response"]
    assert "knee pain" in response
    assert "seated" in response
    assert "Stop" in response
    assert "urgent care" in response
    assert "not clearance" in response
    assert "recovered" not in response
    assert "normal training load" not in response


def test_other_pain_takes_priority_over_workout_advice():
    response = AIEngine().coach({}, "My shoulder hurts. Give me a workout.")["coach_response"]
    assert "affected area" in response
    assert "healthcare professional" in response
    assert "seated light presses" not in response


def test_injuries_in_profile_trigger_safety_response():
    response = AIEngine().coach({"injuries": ["knee injury"]}, "Give me a workout")["coach_response"]
    assert "knee pain" in response
    assert "not clearance" in response


@pytest.mark.parametrize("message", [
    "I have knee pain and can't bear weight. Give me a workout.",
    "I have chest pain during exercise.",
    "My knee has severe pain.",
])
def test_urgent_symptoms_do_not_return_a_workout(message):
    response = AIEngine().coach({}, message)["coach_response"]
    assert "urgent" in response
    assert "Do not exercise" in response
    assert "seated light" not in response


@pytest.mark.parametrize(("message", "expected"), [
    ("How do I recover after training?", "rest day"),
    ("What should I eat?", "protein source"),
    ("Make me a workout", "sets"),
    ("I am a beginner. Give me a bodyweight workout.", "Incline push-ups"),
    ("Give me a 10-minute beginner bodyweight workout.", "about 10 minutes"),
    ("What time is it?", "cannot answer every free-form question"),
])
def test_supported_and_unsupported_questions(message, expected):
    response = AIEngine().coach({}, message)["coach_response"]
    assert expected in response
    assert "Your message:" not in response


def test_beginner_bodyweight_workout_is_structured_and_practical():
    response = AIEngine().coach(
        {"experience": "beginner"},
        "Give me a beginner bodyweight workout.",
    )["coach_response"]
    assert "warm-up" in response.lower()
    assert "2 rounds" in response
    assert "chair squats" in response.lower()
    assert "glute bridges" in response.lower()
    assert "rest" in response.lower()
    assert "Give me a beginner bodyweight workout." not in response


def test_beginner_workout_respects_time_in_user_data():
    response = AIEngine().coach(
        {"experience": "beginner", "available_minutes": 10},
        "Give me a workout.",
    )["coach_response"]
    assert "about 10 minutes" in response
    assert "2 rounds" in response
    assert "15-30 seconds" in response


def test_20_minute_beginner_workout_has_a_complete_time_budget():
    response = AIEngine().coach(
        {"experience": "beginner"},
        "Give me a 20-minute beginner bodyweight workout.",
    )["coach_response"]
    assert "20 minutes total" in response
    assert "Warm-up (3 minutes)" in response
    assert "Main circuit (14 minutes)" in response
    assert "3 rounds" in response
    assert "45-second station" in response
    assert "15 seconds after every station" in response
    assert "60 seconds after rounds 1 and 2" in response
    assert "Cool-down (3 minutes)" in response
    assert "3 + 14 + 3 = 20 minutes" in response
