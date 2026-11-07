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
    ("Make me a workout", "available equipment"),
    ("What time is it?", "cannot answer every free-form question"),
])
def test_supported_and_unsupported_questions(message, expected):
    response = AIEngine().coach({}, message)["coach_response"]
    assert expected in response
    assert "Your message:" not in response
