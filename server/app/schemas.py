from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CoachRegister(BaseModel):
    email: EmailStr
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class CoachLogin(BaseModel):
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class AthleteLogin(BaseModel):
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class AthleteRegister(BaseModel):
    email: EmailStr
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CoachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    login: str
    display_name: str
    created_at: datetime


class AthleteCreate(BaseModel):
    login: str = Field(min_length=1, max_length=120)
    display_name: str = Field(default="", max_length=200)
    password: str = Field(default="", max_length=128)


class AthleteUpdate(BaseModel):
    login: str | None = Field(default=None, min_length=1, max_length=120)
    display_name: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AthleteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    coach_id: str | None
    email: str | None = None
    login: str
    display_name: str
    plan_athlete_id: str | None = None
    created_at: datetime


class AthleteMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    login: str
    display_name: str
    coach_id: str | None
    in_group: bool


class InviteSend(BaseModel):
    login: str = Field(min_length=1, max_length=120)


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    coach_id: str
    target_login: str
    status: str
    last_sent_at: datetime
    coach_display_name: str | None = None


class RosterSyncResponse(BaseModel):
    roster_sync_format_version: int
    coach_id: str
    roster_version: int
    generated_at: str
    members: list[dict]
    pending_invites: list[dict]


class PublishImportResponse(BaseModel):
    publication_id: str
    version: int
    athletes_in_payload: int
    new_athlete_credentials: list[dict[str, str]]


class LatestPlanResponse(BaseModel):
    publication_id: str
    version: int
    publish_format_version: int
    published_at: str | None = None
    imported_at: datetime
    athletes: list[AthleteOut]


class WorkoutLogCreate(BaseModel):
    exercise_id: str = ""
    workout_id: str = ""
    log_date: date
    done: bool = False
    done_as_planned: bool = True
    minutes: int | None = None
    distance_km: float | None = None
    sets_done: int | None = Field(default=None, ge=0, le=999)
    reps_done: int | None = Field(default=None, ge=0, le=9999)
    note: str = ""


class WorkoutLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    athlete_id: str
    exercise_id: str
    workout_id: str
    log_date: date
    done: bool
    done_as_planned: bool
    minutes: int | None
    distance_km: float | None
    sets_done: int | None
    reps_done: int | None
    note: str


class WorkoutSessionLogCreate(BaseModel):
    workout_id: str = Field(min_length=1, max_length=64)
    log_date: date
    total_distance_km: float | None = Field(default=None, ge=0, le=9999)
    speed_distance_km: float | None = Field(default=None, ge=0, le=9999)
    hr_avg: int | None = Field(default=None, ge=30, le=250)
    hr_max: int | None = Field(default=None, ge=30, le=250)
    note: str = ""


class WorkoutSessionLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    athlete_id: str
    workout_id: str
    log_date: date
    total_distance_km: float | None
    speed_distance_km: float | None
    hr_avg: int | None
    hr_max: int | None
    note: str
