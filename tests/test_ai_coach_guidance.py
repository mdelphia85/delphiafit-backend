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


def test_other_pain_returns_a_conservative_workout_without_forcing_a_question():
    response = AIEngine().coach({}, "My shoulder hurts. Give me a workout.")["coach_response"]
    assert "shoulder pain" in response
    assert "easy walking" in response
    assert "healthcare professional" in response
    assert "What area hurts" not in response
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


@pytest.mark.parametrize("prompt", [
    "want to build more muscle, best workouts",
    "best workouts to build muscle",
    "How do I train for hypertrophy?",
    "I want to bulk and add size.",
])
def test_muscle_building_goals_take_priority_over_generic_workouts(prompt):
    response = AIEngine().coach({"experience": "beginner"}, prompt)["coach_response"]
    assert "hypertrophy" in response.lower()
    assert "progressive resistance" in response.lower()
    assert "squat or lunge" in response.lower()
    assert "equipment" in response.lower()
    assert "Beginner bodyweight session" not in response


def test_explicit_bodyweight_muscle_goal_has_progressive_overload_options():
    response = AIEngine().coach({}, "Build muscle with bodyweight workouts at home")["coach_response"]
    assert "bodyweight training" in response
    assert "gradually increase" in response
    assert "2-3" in response
    assert "safe and stable" in response


def test_muscle_goal_nutrition_question_addresses_muscle_specific_food():
    response = AIEngine().coach({}, "What should I eat to build muscle?")["coach_response"]
    assert "muscle growth" in response
    assert "protein-containing" in response


def test_muscle_goal_does_not_override_recovery_or_medical_safety():
    response = AIEngine().coach({}, "Exhausted, need recovery before building muscle")["coach_response"]
    assert "rest day" in response
    assert "2-3 sets" not in response
    response = AIEngine().coach({}, "My knee hurts but I want to build muscle")["coach_response"]
    assert "healthcare professional" in response
    assert "2-3 sets" not in response
    response = AIEngine().coach({}, "Chest pain while lifting, want muscle")["coach_response"]
    assert "Do not exercise" in response


@pytest.mark.parametrize(("message", "expected"), [
    ("lower back pain, what workouts can i do to not stress it out", "easy walking"),
    ("My neck is stiff. Can you give me a workout?", "neck pain"),
    ("My shoulder is injured. What workout can I do?", "easy walking"),
    ("My wrist hurts and I still want to exercise.", "easy walking"),
    ("My knee hurts, help me modify my workout.", "seated"),
    ("I sprained an ankle, what exercises can I do?", "seated"),
    ("Hip pain, can I still train?", "seated"),
    ("My foot aches, suggest a workout.", "seated"),
    ("I bruised my ribs, suggest a workout.", "forceful abdominal bracing"),
    ("I have calf soreness, what training can I do?", "seated"),
    ("Arthritis in my elbow, how can I exercise?", "easy walking"),
    ("I have stomach cramps, what exercises can I do?", "forceful abdominal bracing"),
])
def test_common_ailments_and_injuries_get_condition_aware_options(message, expected):
    response = AIEngine().coach({"fatigue": 3}, message)["coach_response"]
    assert expected.lower() in response.lower()
    assert "Stop if symptoms increase" in response
    assert "What area hurts" not in response
    assert "clearance to train" in response


@pytest.mark.parametrize("message", [
    "I have the flu and a fever, can I work out?",
    "I have a cold and sore throat. Can I go train?",
    "I'm dizzy and nauseous, what workout should I do?",
])
def test_systemic_ailments_do_not_get_strenuous_workouts(message):
    response = AIEngine().coach({}, message)["coach_response"]
    assert "skip a structured" in response
    assert "Rest and recover" in response


def test_headache_and_migraine_do_not_get_generic_fitness_circuit():
    response = AIEngine().coach({}, "I have a migraine. Can I work out?")["coach_response"]
    assert "migraine" in response
    assert "intense workout may aggravate" in response


@pytest.mark.parametrize("message", [
    "Lower back pain with loss of bladder control, help me exercise",
    "Numbness around the groin with back pain, suggest a workout",
    "I have worsening leg weakness, backache and want to train",
])
def test_red_flags_prevent_workout_suggestions(message):
    response = AIEngine().coach({}, message)["coach_response"]
    assert "Do not exercise" in response
    assert "urgent" in response.lower()
    assert "conservative modified workout" not in response


def test_pain_without_a_location_receives_general_guidance_and_one_question():
    response = AIEngine().coach({}, "I have pain and need a workout.")["coach_response"]
    assert "affected area" in response
    assert "What area is affected" in response


def test_multiple_pain_areas_do_not_get_misleading_specific_exercises():
    response = AIEngine().coach({}, "My knee and shoulder hurt. Suggest a workout.")["coach_response"]
    assert "more than one area" in response
    assert "full exercise circuit" in response
