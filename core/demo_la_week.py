"""Демо-план: неделя лёгкой атлетики 12–18.10.2026."""
from __future__ import annotations

from core.models import (
    AnnualPlan,
    AthleteProfile,
    Exercise,
    ExerciseType,
    Macrocycle,
    Mesocycle,
    Microcycle,
    TrainingPlan,
    Workout,
)

WEEK_START = "2026-10-12"


def _ex(
    title: str,
    kind: ExerciseType,
    *,
    minutes: int = 0,
    km: float = 0.0,
    intensity: int = 0,
    zone: str = "",
    weight: float = 0.0,
    sets: int = 0,
    reps: int = 0,
    notes: str = "",
) -> Exercise:
    return Exercise(
        title=title,
        exercise_type=kind,
        duration_minutes=minutes,
        volume_km=km,
        intensity_percent=intensity,
        hr_zone=zone,
        weight_kg=weight,
        sets=sets,
        reps=reps,
        notes=notes,
    )


def _workout(title: str, kind: ExerciseType, exercises: list[Exercise], minutes: int = 0) -> Workout:
    return Workout(
        title=title,
        workout_type=kind,
        duration_minutes=minutes or sum(e.duration_minutes for e in exercises),
        exercises=exercises,
    )


def build_demo_la_week_plan() -> TrainingPlan:
    """Пн–Вс: скорость, сила, техника, выносливость, восстановление; ср/сб — расширенные дни."""
    workouts = [
        _workout(
            "Пн · Скоростная",
            ExerciseType.SPEED,
            [
                _ex("Разминка лёгкий бег", ExerciseType.RECOVERY, minutes=15, km=2.0, zone="Z1"),
                _ex("Ускорения 60 м", ExerciseType.SPEED, sets=6, reps=1, intensity=95, notes="полный отдых 3–4 мин"),
                _ex("Бег с барьерами (техника)", ExerciseType.TECHNICAL, sets=5, reps=3, notes="5 барьеров, низкий темп"),
                _ex("Прыжки на скакалке", ExerciseType.SPEED, sets=3, reps=100),
                _ex("Заминка ходьба", ExerciseType.RECOVERY, minutes=10, km=0.8),
            ],
            minutes=75,
        ),
        _workout(
            "Вт · Силовая",
            ExerciseType.STRENGTH,
            [
                _ex("Присед со штангой", ExerciseType.STRENGTH, sets=4, reps=6, weight=80),
                _ex("Выпады с гантелями", ExerciseType.STRENGTH, sets=3, reps=10, weight=20),
                _ex("Румынская тянга", ExerciseType.STRENGTH, sets=4, reps=8, weight=70),
                _ex("Жим ногами", ExerciseType.STRENGTH, sets=3, reps=12, weight=120),
                _ex("Планка", ExerciseType.STRENGTH, sets=3, reps=1, notes="60 сек"),
            ],
            minutes=70,
        ),
        _workout(
            "Ср · Техническая + ОФП (2 блока)",
            ExerciseType.TECHNICAL,
            [
                _ex("Бег с высоким подниманием бедра", ExerciseType.TECHNICAL, sets=4, reps=30, notes="утро · техника бега"),
                _ex("Прыжки в длину с места", ExerciseType.TECHNICAL, sets=5, reps=4),
                _ex("Махи ногами у опоры", ExerciseType.TECHNICAL, sets=3, reps=12),
                _ex("Кор: скручивания", ExerciseType.STRENGTH, sets=3, reps=20, notes="вечер · ОФП"),
                _ex("Прыжки на тумбу", ExerciseType.STRENGTH, sets=4, reps=6),
            ],
            minutes=85,
        ),
        _workout(
            "Чт · Выносливость",
            ExerciseType.ENDURANCE,
            [
                _ex("Непрерывный бег", ExerciseType.ENDURANCE, minutes=40, km=6.0, zone="Z2", intensity=70),
                _ex("Фартlek 200/200", ExerciseType.TEMPO, sets=8, reps=1, notes="200 м быстро / 200 м трусца"),
                _ex("Бег по пересечёнке", ExerciseType.ENDURANCE, minutes=15, km=2.5, zone="Z2"),
                _ex("Растяжка", ExerciseType.RECOVERY, minutes=15),
                _ex("Пресс и спина", ExerciseType.STRENGTH, sets=3, reps=15),
            ],
            minutes=90,
        ),
        _workout(
            "Пт · Скоростно-силовая",
            ExerciseType.SPEED,
            [
                _ex("Разминка", ExerciseType.RECOVERY, minutes=12, km=1.5),
                _ex("Спринт 100 м", ExerciseType.SPEED, sets=5, reps=1, intensity=98),
                _ex("Прыжки в глубину", ExerciseType.STRENGTH, sets=4, reps=5),
                _ex("Броски медбола", ExerciseType.STRENGTH, sets=4, reps=8, weight=6),
                _ex("Заминка", ExerciseType.RECOVERY, minutes=10),
            ],
            minutes=65,
        ),
        _workout(
            "Сб · Техника барьеров + лёгкий бег (2 блока)",
            ExerciseType.TECHNICAL,
            [
                _ex("Барьерный разбег 3 шага", ExerciseType.TECHNICAL, sets=6, reps=3),
                _ex("Упражнение «резинка» (боковые шаги)", ExerciseType.TECHNICAL, sets=3, reps=10),
                _ex("Кор: боковая планка", ExerciseType.STRENGTH, sets=3, reps=1, notes="45 сек"),
                _ex("Лёгкий бег", ExerciseType.RECOVERY, minutes=25, km=4.0, zone="Z1", notes="вечер"),
                _ex("Скакалка", ExerciseType.RECOVERY, sets=2, reps=150),
            ],
            minutes=80,
        ),
        _workout(
            "Вс · Восстановительная",
            ExerciseType.RECOVERY,
            [
                _ex("Лёгкий бег или велосипед", ExerciseType.RECOVERY, minutes=30, km=4.0, zone="Z1"),
                _ex("Самомассаж / ролл", ExerciseType.RECOVERY, minutes=15),
                _ex("Растяжка бёдер и икр", ExerciseType.RECOVERY, minutes=15),
                _ex("Плавание (по желанию)", ExerciseType.RECOVERY, minutes=20),
            ],
            minutes=60,
        ),
    ]

    micro = Microcycle(
        title="Неделя 12–18.10",
        duration_days=7,
        workouts=workouts,
        start_date=WEEK_START,
    )
    meso = Mesocycle(title="Октябрь · подготовка", duration_weeks=1, microcycles=[micro])
    macro = Macrocycle(title="Осенний сезон 2026", duration_months=1, mesocycles=[meso])
    annual = AnnualPlan(title="Лёгкая атлетика 2026", year=2026, start_date=WEEK_START, macrocycles=[macro])

    athletes = [
        AthleteProfile(display_name="Спортсmen (демо)", login="sportsmen"),
    ]

    return TrainingPlan(
        annual=annual,
        plan_start_date=WEEK_START,
        athletes=athletes,
    )
