from app.services.report_rules import workout_requests_distance


def test_strength_workout_no_distance():
    exercises = [
        {"exercise_type": "Силовое", "planned_km": None, "planned_minutes": None},
    ]
    assert workout_requests_distance(exercises, "Силовое") is False


def test_speed_workout_with_km():
    exercises = [
        {"exercise_type": "Скоростное", "planned_km": 0, "planned_minutes": 0},
        {"exercise_type": "Восстановительное", "planned_km": 2.0, "planned_minutes": 15},
    ]
    assert workout_requests_distance(exercises, "Скоростное") is True


def test_technical_only_reps_no_distance():
    exercises = [
        {"exercise_type": "Скоростное", "sets": 6, "reps": 1},
    ]
    assert workout_requests_distance(exercises, "Скоростное") is False
